import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List
from utils import convert_current_date_to_iso8601, create_unique_id
from models.base_model import BaseModel

class AnnoClassInfoModel(BaseModel):


    FIELD_CATEGORY_ID       = "category_id"   ### hash  
    FIELD_CLASS_NAME        = "class_name"     ### range
    FIELD_CLASS_ID          = "class_id"
    FIELD_CLASS_DES         = "description"

    FIELD_CREATED_TIME       = "created_time"
    FIELD_UPDATED_TIME       = "updated_time" 


    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        
    def create_new_class(self, category_id, class_name):
        class_id = f"{class_name}_{create_unique_id()}"
        item = {
            self.FIELD_CREATED_TIME: convert_current_date_to_iso8601(),
            self.FIELD_UPDATED_TIME: convert_current_date_to_iso8601(),
            self.FIELD_CATEGORY_ID: category_id,
            self.FIELD_CLASS_NAME: class_name,
            self.FIELD_CLASS_ID: class_id
        }
        condition = Attr(self.FIELD_CATEGORY_ID).not_exists() & Attr(self.FIELD_CLASS_NAME).not_exists()
        
        try:
            self.put_item_w_condition(item, condition)
        except Exception as e:
            print(e)
            return False

        return True

    def get_all_AI_default_class(self):
        response = self.table.scan()              
        items = response['Items']     

        return items

    def add_default_AI_class(self, category_id, ls_items):
        ls_item_requests = []
        for item in ls_items:
            item_request = {
                self.FIELD_CATEGORY_ID: category_id,
                self.FIELD_CLASS_NAME: item[self.FIELD_CLASS_NAME],
                self.FIELD_CLASS_ID: item[self.FIELD_CLASS_ID],
                self.FIELD_CREATED_TIME: convert_current_date_to_iso8601(),
                self.FIELD_UPDATED_TIME: convert_current_date_to_iso8601()
            }
            ## add to list requests
            ls_item_requests.append(item_request)
        
        ### batch write to DB
        print("ls_item_requests: ", ls_item_requests)
        self.batch_write(ls_item_requests)

        return

    def add_list_class(self, category_id, ls_class_name):
        ls_ok = []
        ls_fail = []
        for class_name in ls_class_name:
            is_ok = self.create_new_class(category_id, class_name)
            if is_ok:
                ls_ok.append(class_name)
            else:
                ls_fail.append(class_name)
        
        return ls_ok, ls_fail

    def query_all_class_of_category(self, category_id, ls_fields_projection=[]):
        if len(ls_fields_projection) == 0:
            ls_fields_projection = [self.FIELD_CLASS_NAME, self.FIELD_CLASS_ID]

        response = self.table.query(
                KeyConditionExpression=Key(self.FIELD_CATEGORY_ID).eq(category_id),
                ProjectionExpression= ",".join(ls_fields_projection),
            )
        
        return response.get("Items", [])

    
        