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
from utils import create_unique_id, get_bucket_key_from_s3_uri, split_ls_into_batch
# from s3_utils import move_data_s3


class MoveS3DataClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()  
        self.s3 = boto3.client('s3')

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.s3_prefix_prebuild_store = body["s3_prefix_prebuild"]
        self.s3_prefix_created_store = body["s3_prefix_create"]
        self.project_id = body["project_id"]
        self.project_name = body["project_name"]
        self.identity_id = body["identity_id"]
        self.bucket_name = body["bucket_name"]

    def _check_input_value(self):
        pass

    def move_data_s3(self, source, target, bucket_name):
        ls_info = []
        #list all data in s3
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)

        for obj in bucket.objects.filter(Prefix=source):
            if obj.key.endswith('/'):
                continue

            old_source = { 'Bucket': bucket_name,
                        'Key': obj.key}
            # replace the prefix
            new_prefix = target.replace(f"{bucket_name}/", "")
            new_key = f'{new_prefix}/{obj.key.replace(source, "")}'
            s3.meta.client.copy(old_source, bucket_name, new_key)

            ls_info.append((new_key.split('/')[-1], f"{bucket_name}/{new_key}", obj.size))

        return ls_info

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)   
        
        # move data in s3
        ls_info = self.move_data_s3(
            self.s3_prefix_prebuild_store, self.s3_prefix_created_store, self.bucket_name)

        if len(ls_info)>0:
            bucket, folder = get_bucket_key_from_s3_uri(self.s3_prefix_created_store)
            s3_key_path = os.path.join(folder, f"create_sample/RI_{create_unique_id()}.json")
            self.s3.put_object(
                Body=json.dumps(ls_info),
                Bucket= bucket,
                Key= s3_key_path
            )            
        else:
            bucket = None
            s3_key_path = None
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "bucket_name": self.bucket_name,
                    "identity_id": self.identity_id,
                    "project_id": self.project_id,
                    "project_name": self.project_name,
                    "s3_key_path": s3_key_path
                },
            is_in_stepfunction=True
        )
       
def lambda_handler(event, context):

    return MoveS3DataClass().handle(event, context)

    