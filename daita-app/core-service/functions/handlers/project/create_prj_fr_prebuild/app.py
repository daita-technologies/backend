import boto3
import json
import os
import uuid

from config import *
from response import *
from error_messages import *
from utils import convert_current_date_to_iso8601, aws_get_identity_id, get_num_prj
import const

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.prebuild_dataset_model import PrebuildDatasetModel
from models.project_model import ProjectModel, ProjectItem
from boto3.dynamodb.conditions import Key, Attr



class CreatePrebuildDatasetClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')     
        self.client_step_func = boto3.client('stepfunctions')
        self.prebuild_dataset_model = PrebuildDatasetModel(os.environ["T_CONST_PREBUILD_DATASET"])
        self.sm_create_prj_prebuild = os.environ["SM_CREATE_PRJ_PREBUILD"]
        self.project_model = ProjectModel(os.environ["TABLE_PROJECT"])
        self.bucket_name = os.environ["BUCKET_NAME"]

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN] 
        self.name_id_prebuild_dataset = body["name_id_prebuild"]
        self.project_name = body["project_name"]
        self.number_random = body["number_random"]
        self.project_info = body["project_info"]

    def _check_input_value(self): 
        prebuild_dataset = self.prebuild_dataset_model.get_prebuild_dataset(self.name_id_prebuild_dataset)
        if prebuild_dataset is None:
            raise Exception(MESS_ERR_INVALID_PREBUILD_DATASET_NAME.format(self.name_id_prebuild_dataset))
        
        ### check number max
        if self.number_random <= 0 or self.number_random >= prebuild_dataset[PrebuildDatasetModel.FIELD_TOTAL_IMAGES]:
            self.number_random = prebuild_dataset[PrebuildDatasetModel.FIELD_TOTAL_IMAGES]
        if self.number_random > const.MAX_NUM_IMGAGES_CLONE_FROM_PREBUILD_DATASET:
            raise (Exception(
                    f'The number of images in original of project is over the limitation {const.MAX_NUM_IMGAGES_CLONE_FROM_PREBUILD_DATASET}!'))

        ### udpate the link to s3
        self.s3_key = prebuild_dataset[PrebuildDatasetModel.FIELD_S3_KEY]
        self.visual_name = prebuild_dataset[PrebuildDatasetModel.FIELD_VISUAL_NAME]

        ###
        try:
            # check length of projectname and project info
            if len(self.project_name) > const.MAX_LENGTH_PROJECT_NAME_INFO:
                raise Exception(const.MES_LENGTH_OF_PROJECT_NAME)
            if len(self.project_info) > const.MAX_LENGTH_PROJECT_NAME_INFO:
                raise Exception(const.MES_LENGTH_OF_PROJECT_INFO)
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e))
                 
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### check limit project
        num_prj=get_num_prj(identity_id)
        if num_prj >= const.MAX_NUM_PRJ_PER_USER:
            raise Exception(const.MES_REACH_LIMIT_NUM_PRJ)

        ### create project on DB
        _uuid = uuid.uuid4().hex
        project_id = f'{self.project_name}_{_uuid}'
        s3_prefix = f'{self.bucket_name}/{identity_id}/{project_id}'
        db_resource = boto3.resource('dynamodb')
        try:
            is_sample = False
            gen_status = VALUE_STATUS_CREATE_SAMPLE_PRJ_GENERATING
            item = {
                        'ID': _uuid,
                        'project_id': project_id,
                        'identity_id': identity_id,
                        'project_name': self.project_name,
                        's3_prefix': s3_prefix,
                        'project_info': self.project_info,
                        'created_date': convert_current_date_to_iso8601(),
                        'is_sample': is_sample,
                        'gen_status': gen_status
                    }
            condition = Attr(ProjectItem.FIELD_PROJECT_NAME).not_exists() & Attr(ProjectItem.FIELD_IDENTITY_ID).not_exists()
            self.project_model.put_item_w_condition(item, condition=condition)
            
        except db_resource.meta.client.exceptions.ConditionalCheckFailedException as e:
            print('Error condition: ', e)
            raise Exception(MES_DUPLICATE_PROJECT_NAME.format(self.project_name))
            
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e)) 
        
        ### call async step function
        stepfunction_input = {
            "identity_id": identity_id,
            "project_id": project_id,
            "project_name": self.project_name,
            "bucket_name": self.bucket_name,
            "s3_prefix_create": s3_prefix,
            "number_random": self.number_random,
            "s3_prefix_prebuild": self.s3_key if (f"s3://{self.bucket_name}" not in self.s3_key) else self.s3_key.replace(f"s3://{self.bucket_name}/", "")
        }
        response = self.client_step_func.start_execution(
            stateMachineArn=self.sm_create_prj_prebuild,
            input=json.dumps(stepfunction_input)
        )        
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "project_id": project_id,
                    "s3_prefix": s3_prefix,
                    "is_sample": is_sample,
                    "gen_status": gen_status,
                    "project_name": self.project_name
                },
        )

@error_response
def lambda_handler(event, context):

    return CreatePrebuildDatasetClass().handle(event, context)

    