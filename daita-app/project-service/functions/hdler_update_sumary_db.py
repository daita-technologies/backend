import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.project_model import ProjectModel, ProjectItem
from models.project_sum_model import ProjectSumModel
from utils import get_bucket_key_from_s3_uri, split_ls_into_batch

db_client = boto3.client('dynamodb')
db_resource = boto3.resource('dynamodb')

class UpdateSummaryDBClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()  
        self.s3 = boto3.client('s3')
        self.project_sum_model = ProjectSumModel(os.environ["T_PROJECT_SUMMARY"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.identity_id = body[KEY_NAME_IDENTITY_ID]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.project_name = body["project_name"]
        self.total_size = body["total_size"]
        self.count = body["count"]
        self.thu_key = body["thu_key"]
        self.thu_name = body["thu_name"]

    def _check_input_value(self):
        pass

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)   
        
        # update summary information
        try:
            response = db_client.update_item(
                TableName=os.environ["T_PROJECT_SUMMARY"],
                Key={
                    'project_id': {
                        'S': self.project_id
                    },
                    'type': {
                        'S': VALUE_TYPE_DATA_ORIGINAL
                    }
                },
                ExpressionAttributeNames={
                    '#SI': 'total_size',
                    '#COU': 'count',
                    '#TK': 'thu_key',
                    '#TN': 'thu_name'
                },
                ExpressionAttributeValues={
                    ':si': {
                        'N': str(self.total_size)
                    },
                    ':cou': {
                        'N': str(self.count)
                    },
                    ':tk': {
                        'S': self.thu_key
                    },
                    ':tn': {
                        'S': self.thu_name
                    }
                },
                UpdateExpression='SET #TK = :tk, #TN = :tn ADD #SI :si, #COU :cou',
            )
            print('response_summary: ', response)
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e))

        # update generate status
        try:
            table = db_resource.Table(os.environ['T_PROJECT'])
            response = table.update_item(
                Key={
                    'identity_id': self.identity_id,
                    'project_name': self.project_name,
                },
                ExpressionAttributeValues={
                    ':st': VALUE_STATUS_CREATE_SAMPLE_PRJ_FINISH,
                },
                UpdateExpression='SET  gen_status = :st'
            )
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e))
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={},
            is_in_stepfunction=True
        )
       
def lambda_handler(event, context):

    return UpdateSummaryDBClass().handle(event, context)

    