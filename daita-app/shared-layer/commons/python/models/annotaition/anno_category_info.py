import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List
from utils import convert_current_date_to_iso8601, create_unique_id
from models.base_model import BaseModel

class AnnoCategoryInfoModel(BaseModel):

    FIELD_PROJECT_ID        = "project_id"   ### hash
    FIELD_CATEGORY_ID       = "category_id"   ### range
    FIELD_CATEGORY_NAME     = "category_name"
    FIELD_CATEGORY_DES      = "category_des"
    FIELD_S3_KEY_JSON_LABEL = "s3key_jsonlabel"
    FIELD_CREATED_TIME       = "created_time"
    FIELD_UPDATED_TIME       = "updated_time" 


    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        
    def create_new_category(self, project_id, category_name, category_des):
        category_id = f"{category_name}_{create_unique_id()}"
        item = {
            self.FIELD_CREATED_TIME: convert_current_date_to_iso8601(),
            self.FIELD_UPDATED_TIME: convert_current_date_to_iso8601(),
            self.FIELD_PROJECT_ID: project_id,
            self.FIELD_CATEGORY_ID: category_id,
            self.FIELD_CATEGORY_NAME: category_name,
            self.FIELD_CATEGORY_DES: category_des
        }
        condition = Attr(self.FIELD_PROJECT_ID).not_exists() & Attr(self.FIELD_CATEGORY_ID).not_exists()
        self.put_item_w_condition(item, condition)

        return category_id


    def query_all_category_label(self, file_id):
        response = self.table.query(
                KeyConditionExpression=Key(self.FIELD_FILE_ID).eq(file_id),
            )
        
        return response.get("Items", [])

    
        