import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from models.project_model import ProjectModel, ProjectItem
from lambda_base_class import LambdaBaseClass


class ApplyParamExpertModeClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()   
        self.project_model = ProjectModel(os.environ["TABLE_PROJECTS_NAME"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.project_name = body[KEY_NAME_PROJECT_NAME]
        # self.ls_methods_id = body[KEY_NAME_LS_METHOD_ID]
        # self.num_aug_per_imgs = min(MAX_NUMBER_GEN_PER_IMAGES, body.get(KEY_NAME_NUM_AUG_P_IMG, 1)) # default is 1
        # self.data_number = body[KEY_NAME_DATA_NUMBER]  # array of number data in train/val/test  [100, 19, 1]
        self.process_type = body.get(KEY_NAME_PROCESS_TYPE, VALUE_TYPE_METHOD_PREPROCESS)
        self.reference_images = body.get(KEY_NAME_REFERENCE_IMAGES, {})
        self.aug_parameters  = body.get(KEY_NAME_AUG_PARAMS, {})

        ### update value for ls_reference
        for method, s3_link in self.reference_images.items():
            if "s3://" not in s3_link:
                self.reference_images[method] = f"s3://{s3_link}"

    def _check_input_value(self):
        # if len(self.data_number)>0:
        #     if self.data_number[0] == 0:
        #         raise Exception(MESS_NUMBER_TRAINING)        
        # for number in self.data_number:
        #     if number<0:
        #         raise Exception(MESS_NUMBER_DATA)   

        ### if len(ls_reference)>0, it means that we are in the expert mode, 
        ### we will only work with id PRE-2,3,4,5,6,8  
        ### and the code in ls_methods_id much match with code in ls_re
        # TODO

        return    

    def _update_generate_expert_mode_param(self, identity_id, project_name, times_augment, times_preprocess,
                                 reference_images, aug_params):        

        self.project_model.update_generate_expert_mode_param(identity_id, project_name, reference_images,
                                                             aug_params)

        return 
    

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token) 

        

        ### update the times_augment and times_preprocess to DB
        ### update reference images for last running
        self._update_generate_expert_mode_param(identity_id, 
                                                            self.project_name, self.reference_images, self.aug_parameters)          
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={},
        )

        

@error_response
def lambda_handler(event, context):

    return ApplyParamExpertModeClass().handle(event, context)

    