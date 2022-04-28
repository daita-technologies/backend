import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *


class GenerateTaskItem():
    FIELD_IDENTITY_ID = "identity_id"
    FIELD_PROJECT_ID = "project_id"
    FIELD_STATUS = "status"
    FIELD_NUM_VALUE = "num_value"
    FIELD_TASK_ID = "task_id"
    FIELD_TYPE_METHOD = "type_method"
    FIELD_UPDATE_TIME = "updated_time"
    FIELD_NUMBER_FINISHED = "number_finished"
    FIELD_PROJECT_ID = "project_id"
    FIELD_NUM_GEN_IMAGES = "number_gen_images"
    FIELD_CREATE_TIME = "created_time"
    FIELD_PROCESS_TYPE = "process_type"
    FIELD_EXECUTEARN = 'ExecutionArn'

    REQUEST_TYPE_ALL            = "all"
    REQUEST_TYPE_TASK_PROGRESS  = "task_progress"

    def __init__(self) -> None:
        self.identity_id        = ""
        self.task_id            = ""
        self.status             = ""
        self.type_method        = ""
        self.number_finished    = 0
        self.number_gen_images  = 0
        self.project_id         = ""
        self.create_time        = convert_current_date_to_iso8601()
        self.updated_time       = convert_current_date_to_iso8601()
        self.process_type       = ""
        self.executeArn = ""

    def to_dict(self, request = REQUEST_TYPE_ALL):
        print(self.__dict__)
        if request == self.REQUEST_TYPE_TASK_PROGRESS:
            dict_info = {
                self.FIELD_IDENTITY_ID: self.identity_id,
                self.FIELD_TASK_ID: self.task_id,
                self.FIELD_STATUS: self.status,
                self.FIELD_PROCESS_TYPE: self.process_type,
                self.FIELD_NUMBER_FINISHED: self.number_finished,
                self.FIELD_NUM_GEN_IMAGES: self.number_gen_images,
                self.FIELD_PROJECT_ID: self.project_id,
                self.FIELD_EXECUTEARN : self.executeArn
            }
        else:
            dict_info = {
                self.FIELD_IDENTITY_ID: self.identity_id,
                self.FIELD_TASK_ID: self.task_id,
                self.FIELD_STATUS: self.status,
                self.FIELD_TYPE_METHOD: self.type_method,
                self.FIELD_NUMBER_FINISHED: self.number_finished,
                self.FIELD_NUM_GEN_IMAGES: self.number_gen_images,
                self.FIELD_PROJECT_ID: self.project_id,
                self.FIELD_CREATE_TIME: self.create_time,
                self.FIELD_UPDATE_TIME: self.updated_time,
                self.FIELD_PROCESS_TYPE: self.process_type,
                self.FIELD_EXECUTEARN : self.executeArn
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
            self.executeArn         = item_info.get(self.FIELD_EXECUTEARN)
            return self   

    @classmethod
    def create_new_generate_task(cls, identity_id, project_id, type_method):
        object = cls()
        object.task_id = create_task_id_w_created_time()
        object.type_method = type_method
        object.process_type = type_method
        object.status = VALUE_GENERATE_TASK_STATUS_PENDING
        object.identity_id = identity_id
        object.project_id = project_id
        
        return object



class GenerateTaskModel():    

    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name)        

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

    def insert_new_generate_task(self, item) -> None:
        response = self.table.put_item(
                Item = item.to_dict()                               
            ) 
        
        return

    def create_new_generate_task(self, identity_id, project_id, type_method):
        generate_task_item = GenerateTaskItem.create_new_generate_task(identity_id, project_id, type_method)
        self.insert_new_generate_task(generate_task_item)

        return generate_task_item.task_id
    
    def update_status(self,identity_id, task_id,status):
        self.table.update_item(
            Key={
                GenerateTaskItem.FIELD_IDENTITY_ID: identity_id,
                GenerateTaskItem.FIELD_TASK_ID: task_id,
            },
            UpdateExpression="SET #s=:s ",
            ExpressionAttributeValues={
                ':s': status
            },
            ExpressionAttributeNames={
                '#s': 'status',
            }
        )
    def update_ExecutionArn(self,identity_id, task_id,executionArn):
        self.table.update_item(
            Key={
                GenerateTaskItem.FIELD_IDENTITY_ID: identity_id,
                GenerateTaskItem.FIELD_TASK_ID: task_id,
            },
            UpdateExpression="SET #e=:e ",
            ExpressionAttributeValues={
                ':e': executionArn
            },
            ExpressionAttributeNames={
                '#e': 'ExecutionArn',
            }
        )
    
