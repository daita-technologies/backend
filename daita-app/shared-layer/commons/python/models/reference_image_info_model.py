from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List
from utils import convert_current_date_to_iso8601


class ReferenceImageInfoModel():
    
    FIELD_PROJECT_ID        = "project_id"
    FIELD_METHOD_ID         = "method_id"
    FIELD_S3_IMAGE_PATH     = "image_s3_path" 
    FIELD_TASK_ID           = "task-id"   # use for tracking if error hapends
    FIELD_CREATE_TIME       = "created_time"  
    FIELD_UPDATED_TIME      = "updated_time"
    
    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        
    def insert_new_item(self, item) -> None:
        response = self.table.put_item(
                Item = item                               
            ) 
        return      

    def create_reference_info(self, project_id, reference_info: dict, task_id = ""):       
        for method_id, value in reference_info.items():
            info_item = {
                self.FIELD_PROJECT_ID: project_id,
                self.FIELD_METHOD_ID: method_id,
                self.FIELD_S3_IMAGE_PATH: value["s3_path"],
                self.FIELD_CREATE_TIME: convert_current_date_to_iso8601(),
                self.FIELD_TASK_ID: task_id
            }  
            self.insert_new_item(info_item)

        return 
    
    def get_info_of_project(self, project_id):
        response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id)                
            )
        items = response["Items"]        
                    
        return items        