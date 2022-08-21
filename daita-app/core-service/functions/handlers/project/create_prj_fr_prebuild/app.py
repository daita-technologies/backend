import boto3
import json
import os
import uuid

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.prebuild_dataset_model import PrebuildDatasetModel


class CreatePrebuildDatasetClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')     
        self.client_step_func = boto3.client('stepfunctions')
        self.prebuild_dataset_model = PrebuildDatasetModel(os.environ["T_CONST_PREBUILD_DATASET"])
        self.sm_create_prj_prebuild = os.environ["SM_CREATE_PRJ_PREBUILD"]

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN] 
        self.name_id_prebuild_dataset = body["name_id_prebuild"]
        self.number_random = body["number_random"]

    def _check_input_value(self): 
        prebuild_dataset = self.prebuild_dataset_model.get_prebuild_dataset(self.name_id_prebuild_dataset)
        if prebuild_dataset is None:
            raise Exception(MESS_ERR_INVALID_PREBUILD_DATASET_NAME.format(self.name_id_prebuild_dataset))
        
        ### check number max
        if self.number_random <= 0 or self.number_random >= prebuild_dataset[PrebuildDatasetModel.FIELD_TOTAL_IMAGES]:
            self.number_random = prebuild_dataset[PrebuildDatasetModel.FIELD_TOTAL_IMAGES]

        ### udpate the link to s3
        self.s3_key = prebuild_dataset[PrebuildDatasetModel.FIELD_S3_KEY]
        self.visual_name = prebuild_dataset[PrebuildDatasetModel.FIELD_VISUAL_NAME]
                 
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### create project on DB
        _uuid = uuid.uuid4().hex
        project_id = f'{self.visual_name}_{_uuid}'
        s3_prefix = f'{os.environ["BUCKET_NAME"]}/{identity_id}/{project_id}'
        db_client = boto3.client('dynamodb')
        db_resource = boto3.resource('dynamodb')
        try:
            is_sample = True
            gen_status = "GENERATING"
            table_prj = db_resource.Table(os.environ["T_PROJECT"])
            table_prj.put_item(
                    Item = {
                        'ID': _uuid,
                        'project_id': project_id,
                        'identity_id': identity_id,
                        'project_name': project_name,
                        's3_prefix': s3_prefix,
                        'project_info': project_info,
                        # 'sub': sub,
                        'created_date': convert_current_date_to_iso8601(),
                        'is_sample': is_sample,
                        'gen_status': gen_status
                    },
                    ConditionExpression = Attr('project_name').not_exists() & Attr('identity_id').not_exists()
                )
            
        except db_resource.meta.client.exceptions.ConditionalCheckFailedException as e:
            print('Error condition: ', e)
            err_mess = const.MES_DUPLICATE_PROJECT_NAME.format(project_name)
            return convert_response({"error": True, 
                    "success": False, 
                    "message": err_mess, 
                    "data": None})
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True, 
                    "success": False, 
                    "message": repr(e), 
                    "data": None})
        
        ### call async step function
        stepfunction_input = {
            "identity_id": identity_id,
            "id_token": self.id_token,
        }
        response = self.client_step_func.start_execution(
            stateMachineArn=self.sm_create_prj_prebuild,
            input=json.dumps(stepfunction_input)
        )        
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={},
        )

@error_response
def lambda_handler(event, context):

    return CreatePrebuildDatasetClass().handle(event, context)

    