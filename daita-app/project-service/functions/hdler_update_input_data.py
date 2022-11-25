import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.data_model import DataModel, DataItem
from models.task_model import TaskModel
from utils import get_bucket_key_from_s3_uri, split_ls_into_batch, convert_current_date_to_iso8601

db_resource = boto3.resource('dynamodb')

class MoveUpdateDataClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()  
        self.s3 = boto3.client('s3')

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.identity_id = body[KEY_NAME_IDENTITY_ID]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.bucket_name = body["bucket_name"]   
        self.s3_key_path = body["s3_key_path"]
        self.project_name = body["project_name"]

    def _check_input_value(self):
        pass

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)   
        
        resultS3 = self.s3.get_object(Bucket=self.bucket_name, Key=self.s3_key_path)
        ls_info = json.loads(resultS3["Body"].read().decode())

        # update to DB
        # create the batch request from input data and summary the information
        ls_item_request = []
        total_size = 0
        count = 0
        for object in ls_info:
            # update summary information
            size_old = 0
            total_size += (object[2]-size_old)
            if size_old <= 0:
                count += 1

            is_ori = True
            type_method = VALUE_TYPE_DATA_ORIGINAL
            item_request = {
                'project_id': self.project_id,  # partition key
                's3_key': object[1],          # sort_key
                'filename': object[0],
                'hash': '',      # we use function get it mean that this field is optional in body
                'size': object[2],              # size must be in Byte unit
                'is_ori':  True,
                'type_method': type_method,
                'gen_id': '',  # id of generation method
                'created_date': convert_current_date_to_iso8601()
            }
            ls_item_request.append(item_request)

        try:
            table = db_resource.Table(os.environ["T_DATA_ORI"])
            with table.batch_writer() as batch:
                for item in ls_item_request:
                    batch.put_item(Item=item)
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e))
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "total_size": total_size,
                    "count": count,
                    "thu_key": ls_item_request[0]['s3_key'],
                    "thu_name": ls_item_request[0]['filename'],
                    "project_id": self.project_id,
                    "project_name": self.project_name,
                    "identity_id": self.identity_id
                },
            is_in_stepfunction=True
        )
       
def lambda_handler(event, context):

    return MoveUpdateDataClass().handle(event, context)

    