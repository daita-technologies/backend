import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *
from decimal import Decimal

from system_parameter_store import SystemParameterStore
from models.generate_task_model import GenerateTaskModel
from models.project_model import ProjectModel, ProjectItem
from models.project_sum_model import ProjectSumModel
from lambda_base_class import LambdaBaseClass
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


class GenerateImageClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()   
        self.project_model = ProjectModel(os.environ["TABLE_PROJECTS_NAME"])
        self.generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])
        self.project_sum_model = ProjectSumModel(os.environ["TABLE_PROJECT_SUMMARY"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.project_name = body[KEY_NAME_PROJECT_NAME]
        self.ls_methods_id = body[KEY_NAME_LS_METHOD_ID]
        self.data_type = body.get(KEY_NAME_DATA_TYPE, 'ORIGINAL')  # type is one of ORIGINAL or PREPROCESS, default is original        
        self.num_aug_per_imgs = min(MAX_NUMBER_GEN_PER_IMAGES, body.get(KEY_NAME_NUM_AUG_P_IMG, 1)) # default is 1
        self.data_number = body[KEY_NAME_DATA_NUMBER]  # array of number data in train/val/test  [100, 19, 1]
        self.process_type = body.get(KEY_NAME_PROCESS_TYPE, VALUE_TYPE_METHOD_PREPROCESS)
        self.reference_images = body.get(KEY_NAME_REFERENCE_IMAGES, {})
        self.aug_parameters  = body.get(KEY_NAME_AUG_PARAMS, {})
        self.is_normalize_resolution = body.get(KEY_NAME_IS_RESOLUTION, False)        

        ### update value for ls_reference
        for method, s3_link in self.reference_images.items():
            if "s3://" not in s3_link:
                self.reference_images[method] = f"s3://{s3_link}"

    def _check_input_value(self):
        if len(self.data_number)>0:
            if self.data_number[0] == 0:
                raise Exception(MESS_NUMBER_TRAINING)        
        for number in self.data_number:
            if number<0:
                raise Exception(MESS_NUMBER_DATA)   

        ### if len(ls_reference)>0, it means that we are in the expert mode, 
        ### we will only work with id PRE-2,3,4,5,6,8  
        ### and the code in ls_methods_id much match with code in ls_re
        # TODO

        return

    def _check_running_task(self, generate_task_model:GenerateTaskModel, identity_id, project_id):
        """
        Check any running tasks of this project
        """   
        ls_running_task = generate_task_model.query_running_tasks(identity_id, project_id)  
        if len(ls_running_task) > 0:
            raise Exception(MESS_ERROR_OVER_LIMIT_RUNNING_TASK)

        return ls_running_task

    def _get_type_method(self, ls_methods_id):
        type_method = VALUE_TYPE_METHOD_PREPROCESS
        if len(ls_methods_id)==0:
            return self.process_type

        if VALUE_TYPE_METHOD_NAME_AUGMENT in ls_methods_id[0]:
            type_method = VALUE_TYPE_METHOD_AUGMENT
        elif VALUE_TYPE_METHOD_NAME_PREPROCESS in ls_methods_id[0]:
            type_method = VALUE_TYPE_METHOD_PREPROCESS
        else:
            raise Exception(MESS_ERR_INVALID_LIST_METHOD)
        
        return type_method

    def _check_generate_times_limitation(self, identity_id, project_name, type_method):        
        project_rec = self.project_model.get_project_info(identity_id, project_name)
        if project_rec is None:
            raise Exception(MESS_PROJECT_NOT_FOUND.format(project_name))
            
        times_generated = int(project_rec.get_value_w_default(ProjectItem.FIELD_TIMES_AUGMENT, 0))
        times_preprocess = int(project_rec.get_value_w_default(ProjectItem.FIELD_TIMES_PREPRO, 0))
        s3_prefix = project_rec.__dict__[ProjectItem.FIELD_S3_PREFIX]        

        if type_method == VALUE_TYPE_METHOD_AUGMENT: 
            if times_generated >= int(self.const.get_param(os.environ["LIMIT_AUGMENT_TIMES"])):
                raise Exception(MESS_REACH_LIMIT_AUGMENT.format(self.const.get_param(os.environ["LIMIT_AUGMENT_TIMES"])))    
        elif type_method == VALUE_TYPE_METHOD_PREPROCESS:
            if times_preprocess >= int(self.const.get_param(os.environ["LIMIT_PROCESSING_TIMES"])):
                raise Exception(MESS_REACH_LIMIT_PREPROCESS.format(self.const.get_param(os.environ["LIMIT_PROCESSING_TIMES"])))

        return times_generated, times_preprocess, s3_prefix

    def _update_generate_times(self, identity_id, project_name, type_method, times_augment, times_preprocess,
                                 reference_images, aug_params):
        if type_method == VALUE_TYPE_METHOD_PREPROCESS:
            times_preprocess += 1
        elif type_method == VALUE_TYPE_METHOD_AUGMENT:
            times_augment += 1

        ### update float to Decimal
        aug_params = json.loads(json.dumps(aug_params), parse_float=Decimal)

        self.project_model.update_project_generate_times(identity_id, project_name, times_augment,
                                                             times_preprocess, reference_images,
                                                             aug_params)

        return times_preprocess, times_augment

    def _create_task(self, identity_id, project_id, type_method):
        # create task id
        task_id = self.generate_task_model.create_new_generate_task(identity_id, project_id, type_method)
        return task_id 
      
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

    def _update_ls_method_for_preprocessing(self, ls_method_id):
        if "PRE-001" in ls_method_id:
            for method in list(ls_method_id):
                if method not in LS_METHOD_KEEP_IF_EXIST_PRE001:
                    ls_method_id.remove(method)
        return ls_method_id

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token) 

        ### check running task        
        self._check_running_task(self.generate_task_model, identity_id, self.project_id)        
        
        ### get type of process
        type_method = self._get_type_method(self.ls_methods_id)

        ### update the ls_method_id for preprocess
        if type_method == VALUE_TYPE_METHOD_PREPROCESS:
            self.ls_methods_id = self._update_ls_method_for_preprocessing(self.ls_methods_id)
            print(f"ls_method_id after updating: {self.ls_methods_id}")

        ### check generate times limitation and get times of preprocess and augment
        times_augment, times_preprocess, s3_prefix = self._check_generate_times_limitation(
                                                        identity_id, self.project_name, type_method)

        ### update the times_augment and times_preprocess to DB
        ### update reference images for last running
        times_preprocess, times_augment = self._update_generate_times(identity_id, 
                                                            self.project_name, type_method, 
                                                            times_augment, times_preprocess, self.reference_images, self.aug_parameters) 

        ### update data number in case auto split for augmentation
        if type_method == VALUE_TYPE_METHOD_AUGMENT:
            self.project_model.update_project_info(identity_id, self.project_name, self.data_type, self.data_number)      

        ### check if preprocess then reset in prj sumary
        if type_method == VALUE_TYPE_METHOD_PREPROCESS:
            self.project_sum_model.reset_prj_sum_preprocess(project_id = self.project_id, 
                                                            type_data=VALUE_TYPE_DATA_PREPROCESSED)

            ##delete image in preprocess table
            db_resource = boto3.resource('dynamodb',REGION)
            preprocessTBL = db_resource.Table(os.environ['TABLE_PREPROCESS'])
            queryResponse = preprocessTBL.query(
            KeyConditionExpression=Key('project_id').eq(self.project_id)
            )
            print(f"The number of files in preproces table {len(queryResponse['Items'])}")
            with preprocessTBL.batch_writer() as batch:
                for each in queryResponse['Items']:
                    preprocessTBL.delete_item(Key={
                        'project_id': each['project_id'],
                        'filename':each['filename']
                    })

        ### create taskID and update to DB
        task_id = self._create_task(identity_id, self.project_id, type_method)

        ### push event to eventbridge
        detail_pass_para = {
            KEY_NAME_IDENTITY_ID: identity_id,
            KEY_NAME_PROJECT_ID: self.project_id,
            KEY_NAME_PROJECT_NAME: self.project_name,
            KEY_NAME_LS_METHOD_ID: self.ls_methods_id,
            KEY_NAME_DATA_TYPE: self.data_type,
            KEY_NAME_DATA_NUMBER: self.data_number,
            KEY_NAME_S3_PREFIX: s3_prefix,
            KEY_NAME_TIMES_AUGMENT: times_augment,
            KEY_NAME_TIMES_PREPROCESS: times_preprocess,
            KEY_NAME_TASK_ID: task_id,
            KEY_NAME_ID_TOKEN: self.id_token,
            KEY_NAME_PROCESS_TYPE: type_method,
            KEY_NAME_REFERENCE_IMAGES: self.reference_images,
            KEY_NAME_IS_RESOLUTION: self.is_normalize_resolution,
            KEY_NAME_AUG_PARAMS: self.aug_parameters
        }
        event_id = self._put_event_bus(detail_pass_para) 
        message = "OK"
        status_code = HTTPStatus.OK
        sqsClient = boto3.client('sqs',REGION)
        
        def getQueue(queue_name_env):
            try:
                response = sqsClient.get_queue_url(QueueName=queue_name_env)
            except ClientError as e:
                print(e)
                raise e
            return response['QueueUrl']
        def countTaskInQueue(queue_id):
            response = sqsClient.get_queue_attributes(
                                    QueueUrl=getQueue(queue_id),
                                    AttributeNames=[
                                        'ApproximateNumberOfMessages'
                                    ]
                                )
            num_task_in_queue = response['Attributes']['ApproximateNumberOfMessages']
            print(f"QueueID:  {queue_id} has len: {num_task_in_queue}")
            return int(num_task_in_queue)        
        QueueResq = countTaskInQueue(os.environ['QUEUE'])
        print(QueueResq)
        if QueueResq > int(os.environ['MAX_CONCURRENCY_TASK']):
            message = "The system is limited, Please waiting."
            status_code = HTTP_STATUS_WARNING

        return generate_response(
            message=message,
            status_code=status_code,
            data={
                KEY_NAME_TASK_ID: task_id,
                KEY_NAME_TIMES_AUGMENT: times_augment,
                KEY_NAME_TIMES_PREPROCESS: times_preprocess
            },
        )

        

@error_response
def lambda_handler(event, context):

    return GenerateImageClass().handle(event, context)

    