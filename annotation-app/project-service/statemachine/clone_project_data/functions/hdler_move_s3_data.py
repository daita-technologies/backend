import boto3
import json
import os
import random

from config import *
from response import *
from error_messages import *
from identity_check import *
from s3_utils import separate_s3_uri

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.data_model import DataModel, DataItem

from utils import create_unique_id, get_bucket_key_from_s3_uri, split_ls_into_batch

class MoveS3DataClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()  
        self.s3 = boto3.client('s3')

        self.daita_data_original_model = DataModel(self.env.TABLE_DAITA_DATA_ORIGINAL)

    @LambdaBaseClass.parse_body
    def parser(self, body):

        self.logger.debug(f"body in main_parser: {body}")

        self.s3_prefix_created_store = body["s3_prefix_create"]   ### s3 of anno, where store image
        self.anno_project_id = body["anno_project_id"]
        self.anno_project_name = body["anno_project_name"]
        self.identity_id = body["identity_id"]
        self.daita_project_id = body["daita_project_id"]

    def _check_input_value(self):
        pass

    def move_data_s3(self):
        """
        Move data original of daita project to anno project 
        """
        ls_info = []


        #get all data in original data of daita project
        ls_task_params = []
        ls_data_original_items = self.daita_data_original_model.get_all_data_in_project(self.daita_project_id)

        for obj in ls_data_original_items:
            old_key = separate_s3_uri(obj[DataItem.FIELD_S3_KEY], self.env.S3_DAITA_BUCKET_NAME)[1]
            old_source = { 'Bucket': self.env.S3_DAITA_BUCKET_NAME,
                        'Key': old_key}
            new_key = os.path.join(separate_s3_uri(self.s3_prefix_created_store, self.env.S3_ANNO_BUCKET_NAME)[1], old_key.split("/")[-1])
            size = obj[DataItem.FIELD_SIZE]

            ### copy data to new s3 folder
            boto3.resource('s3').meta.client.copy(old_source, self.env.S3_ANNO_BUCKET_NAME, new_key)

            ## add to list info 
            ls_info.append((new_key.split('/')[-1], f"{self.env.S3_ANNO_BUCKET_NAME}/{new_key}", size))

        return ls_info

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)   
        
        # move data in s3
        ls_info = self.move_data_s3()

        if len(ls_info)>0:
            bucket, folder = get_bucket_key_from_s3_uri(self.s3_prefix_created_store)
            s3_key_path = os.path.join(folder, f"clone_project/RI_{create_unique_id()}.json")
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
                    "identity_id": self.identity_id,
                    "anno_project_id": self.anno_project_id,
                    "anno_project_name": self.anno_project_name,
                    "s3_key_path": s3_key_path
                },
            is_in_stepfunction=True
        )
       
def lambda_handler(event, context):

    return MoveS3DataClass().handle(event, context)

    