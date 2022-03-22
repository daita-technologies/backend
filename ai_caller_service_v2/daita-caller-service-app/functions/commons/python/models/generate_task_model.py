import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *


class GenerateTaskItem():
    FIELD_IDENTITY_ID = "identity_id"
    FIELD_PROJECT_ID = "project_id"
    FIELD_STATUS = "status"
    FIELD_NUM_VALUE = "num_value"
    FIELD_TASK_ID = "task_id"
    FIELD_PROCESS_TYPE = "process_type"
    FIELD_UPDATE_TIME = "updated_time"
    FIELD_NUMBER_FINISHED = "number_finished"
    FIELD_PROJECT_ID = "project_id"
    FIELD_NUM_GEN_IMAGES = "number_gen_images"
    FIELD_CREATE_TIME = "created_time"

    def __init__(self) -> None:
        self.identity_id        = ""
        self.task_id            = ""
        self.updated_time       = ""
        self.status             = ""
        self.process_type       = ""
        self.number_finished    = 0
        self.number_gen_images  = 0
        self.project_id         = ""


    def to_dict(self):
        print(self.__dict__)
        dict_info = {
            self.FIELD_IDENTITY_ID: self.identity_id,
            self.FIELD_TASK_ID: self.task_id,
            self.FIELD_STATUS: self.status,
            self.FIELD_PROCESS_TYPE: self.process_type,
            self.FIELD_NUMBER_FINISHED: self.number_finished,
            self.FIELD_NUM_GEN_IMAGES: self.number_gen_images,
            self.FIELD_PROJECT_ID: self.project_id
        }
        return dict_info

    def from_db_item(self, item_info):
        if item_info is None:
            return None
        else:
            self.identity_id        = item_info.get(self.FIELD_IDENTITY_ID)
            self.task_id            = item_info.get(self.FIELD_TASK_ID)
            self.updated_time       = item_info.get(self.FIELD_UPDATE_TIME)
            self.status             = item_info.get(self.FIELD_STATUS)
            self.process_type       = item_info.get(self.FIELD_PROCESS_TYPE)
            self.number_finished    = int(item_info.get(self.FIELD_NUMBER_FINISHED))
            self.number_gen_images  = int(item_info.get(self.FIELD_NUM_GEN_IMAGES))
            self.project_id         = item_info.get(self.FIELD_PROJECT_ID)

            return self        

class GenerateTaskModel():    

    def __init__(self) -> None:
        self.table = boto3.resource('dynamodb').Table(DB_GENERATE_TASK_TABLE_NAME)        
   
    def query_running_tasks(self, identity_id, project_id):
        response = self.table.query (
                KeyConditionExpression=Key(GenerateTaskItem.FIELD_IDENTITY_ID).eq(identity_id),
                FilterExpression=Attr(GenerateTaskItem.FIELD_PROJECT_ID).eq(project_id) & 
                                Attr(GenerateTaskItem.FIELD_STATUS).ne(VALUE_GENERATE_TASK_STATUS_FINISH) & 
                                Attr(GenerateTaskItem.FIELD_STATUS).ne(VALUE_GENERATE_TASK_STATUS_ERROR)
            )
        return response.get("Items", [])

    def get_task_info(self, identity_id, task_id)->GenerateTaskItem:
        response = self.table.get_item(
            Key={
                GenerateTaskItem.FIELD_IDENTITY_ID: identity_id,
                GenerateTaskItem.FIELD_TASK_ID: task_id,
            }
        )    
        item = GenerateTaskItem().from_db_item(response.get('Item', None))
        return item      
            