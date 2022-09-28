import boto3
import json
import os
import random


from response import *

from lambda_base_class import LambdaBaseClass

class MoveS3DataClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')  
        self.s3 = boto3.client('s3')

    @LambdaBaseClass.parse_body
    def parser(self, body):

        print(f"body in main_parser: {body}")

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
        
       
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "test": "test123 value"
                },
            is_in_stepfunction=True
        )
       
def lambda_handler(event, context):

    return MoveS3DataClass().handle(event, context)

    