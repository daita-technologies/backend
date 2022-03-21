import boto3
import json
import datetime

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from models.generate_task_model import GenerateTaskModel
from models.project_model import ProjectModel, ProjectItem

import logging



class HandlerClass():

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(os.environ["LOGGING"]) 
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()   

    def _parse_body(self, event):
        ### parse parameter from body input   
        try:    
            body = json.loads(event['body'])
            self.logger.info("Body: \n", body)

            self.id_token = body[KEY_NAME_ID_TOKEN]
            self.project_id = body[KEY_NAME_PROJECT_ID]
            self.project_name = body[KEY_NAME_PROJECT_NAME]
            self.ls_methods_id = body[KEY_NAME_LS_METHOD_ID]
            self.data_type = body.get(KEY_NAME_DATA_TYPE, 'ORIGINAL')  # type is one of ORIGINAL or PREPROCESS, default is original        
            self.num_aug_per_imgs = min(MAX_NUMBER_GEN_PER_IMAGES, body.get(KEY_NAME_NUM_AUG_P_IMG, 1)) # default is 1
            self.data_number = body[KEY_NAME_DATA_NUMBER]  # array of number data in train/val/test  [100, 19, 1]
        except Exception as e:
            raise Exception(MESS_INVALID_JSON_INPUT) from e
        
        return

    def _get_identity(self, id_token):
        return aws_get_identity_id(id_token)

    def _check_input_value(self):
        if len(self.data_number)>0:
            if self.data_number[0] == 0:
                raise Exception(MESS_NUMBER_TRAINING)        
        for number in self.data_number:
            if number<0:
                raise Exception(MESS_NUMBER_DATA)
            
        if len(self.ls_methods_id) == 0:
            raise Exception(MESS_LIST_METHODS_EMPTY)

        return

    def _check_running_task(self, generate_task_model:GenerateTaskModel, identity_id, project_id):
        """
        Check any running tasks of this project
        """   
        ls_running_task = generate_task_model.get_running_tasks(identity_id, project_id)  
        if len(ls_running_task) > 0:
            raise Exception(MESS_ERROR_OVER_LIMIT_RUNNING_TASK)

        return ls_running_task

    def _get_type_method(self, ls_methods_id):
        type_method = VALUE_TYPE_METHOD_PREPROCESS
        if VALUE_TYPE_METHOD_NAME_AUGMENT in ls_methods_id[0]:
            type_method = VALUE_TYPE_METHOD_AUGMENT
        elif VALUE_TYPE_METHOD_NAME_PREPROCESS in ls_methods_id[0]:
            type_method = VALUE_TYPE_METHOD_PREPROCESS
        else:
            raise Exception(MESS_ERR_INVALID_LIST_METHOD)
        
        return type_method

    def _check_generate_times_limitation(self, identity_id, project_name, type_method):
        project_model = ProjectModel()
        project_rec = project_model.get_project_info(identity_id, project_name)
        times_generated = int(project_rec.get_value_w_default(ProjectItem.FIELD_TIMES_AUGMENT, 0))
        times_preprocess = int(project_rec.get_value_w_default(ProjectItem.FIELD_TIMES_PREPRO, 0))
        s3_prefix = project_rec.__dict__[ProjectItem.FIELD_S3_PREFIX]        

        if type_method == VALUE_TYPE_METHOD_AUGMENT: 
            if times_generated >= int(self.const.limit_augment_times):
                raise Exception(MESS_REACH_LIMIT_AUGMENT.format(self.const.limit_augment_times))    
        elif type_method == VALUE_TYPE_METHOD_PREPROCESS:
            if times_preprocess >= int(self.const.limit_prepro_times):
                raise Exception(MESS_REACH_LIMIT_PREPROCESS.format(self.const.limit_prepro_times))

        return times_generated, times_preprocess, s3_prefix

    def _put_event_bus(self, detail_pass_para):        
        response = self.client_events.put_events(
                        Entries=[
                            {
                                'Source': 'source.events',
                                'DetailType': 'lambda.event',
                                'Detail': json.dumps(detail_pass_para),
                                'EventBusName': os.environ["EVENT_BUS_NAME"]
                            },
                        ]
                    )
        entries = response["Entries"]

        return entries[0]["EventId"]

     
    def process_event(self, event, context):
        
        ### parse body
        self._parse_body(event)

        ### check identity
        identity_id = self._get_identity(self.id_token)
        
        ### check input value
        self._check_input_value()

        ### check running task
        generate_task_model = GenerateTaskModel()
        self._check_running_task(generate_task_model, identity_id, self.project_id)
        
        ### get type of process
        type_method = self._get_type_method(self.ls_methods_id)

        ### check generate times limitation and get times of preprocess and augment
        times_augment, times_preprocess, s3_prefix = self._check_generate_times_limitation(identity_id, self.project_name, type_method)   

        ### push event to eventbridge
        detail_pass_para = {
            KEY_NAME_PROJECT_ID: self.project_id,
            KEY_NAME_PROJECT_NAME: self.project_name,
            KEY_NAME_LS_METHOD_ID: self.ls_methods_id,
            KEY_NAME_DATA_TYPE: self.data_type,
            KEY_NAME_DATA_NUMBER: self.data_number,
            KEY_NAME_S3_PREFIX: s3_prefix,
            KEY_NAME_TIMES_AUGMENT: times_augment+1,
            KEY_NAME_TIMES_PREPROCESS: times_preprocess+1
        }
        event_id = self._put_event_bus(detail_pass_para) 
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                KEY_NAME_TASK_ID: event_id,
                KEY_NAME_TIMES_AUGMENT: (times_augment+1),
                KEY_NAME_TIMES_PREPROCESS: (times_preprocess+1)
            },
        )

@error_response
def lambda_handler(event, context):

    return HandlerClass().process_event(event, context)

    