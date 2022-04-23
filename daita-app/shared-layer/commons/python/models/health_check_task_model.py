import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from error_messages import *
from typing import List
from utils import create_unique_id, convert_current_date_to_iso8601, create_task_id_w_created_time

class HealthCheckTaskItem():
    
    FIELD_TASK_ID       = "task_id"
    FIELD_IDENTITY_ID   = "identity_id"
    FIELD_PROJECT_ID    = "project_id"
    FIELD_DATA_TYPE     = "data_type"
    FIELD_STATUS        = "status"
    FIELD_CREATE_TIME   = "created_time"
    FIELD_UPDATE_TIME   = "updated_time"
    FIELD_PROCESS_TYPE  = "process_type"
    
    REQUEST_TYPE_ALL            = "all"

    def __init__(self) -> None:   
        self.task_id        = ""
        self.identity_id    = ""  
        self.data_type      = ""
        self.project_id     = ""
        self.status         = ""
        self.create_time    = convert_current_date_to_iso8601()
        self.updated_time   = convert_current_date_to_iso8601()
        self.process_type   = VALUE_PROCESS_TYPE_HEALTHCHECK
                
    def to_dict(self, request = REQUEST_TYPE_ALL):
        print(self.__dict__)
        if request == self.REQUEST_TYPE_ALL:
            dict_info = {
                self.FIELD_IDENTITY_ID: self.identity_id,
                self.FIELD_TASK_ID: self.task_id,
                self.FIELD_STATUS: self.status,                
                self.FIELD_PROJECT_ID: self.project_id,
                self.FIELD_DATA_TYPE: self.data_type,
                self.FIELD_CREATE_TIME: self.create_time,
                self.FIELD_UPDATE_TIME: self.updated_time,
                self.FIELD_PROCESS_TYPE: self.process_type
            }
        return dict_info
        

    @classmethod
    def from_db_item(cls, item_info):
        if item_info is None:
            return None
        else:
            object = cls()
            object.item_db = item_info

            object.method_id          = item_info.get(object.FIELD_METHOD_ID)
            object.method_name        = item_info.get(object.FIELD_METHOD_NAME)       

            return object    
        
    @classmethod
    def create_new_healthcheck_task(cls, identity_id, project_id, data_type):
        object = cls()
        object.task_id = create_task_id_w_created_time()
        object.data_type = data_type
        object.status = VALUE_HEALTHCHECK_TASK_STATUS_RUNNING
        object.identity_id = identity_id
        object.project_id = project_id
        object.process_type = VALUE_PROCESS_TYPE_HEALTHCHECK
        return object


class HealthCheckTaskModel():
    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        
    def insert_new_item(self, item) -> None:
        response = self.table.put_item(
                Item = item.to_dict()                               
            ) 
        
        return
    
    def _get_item(self, identity_id, task_id):
        response = self.table.get_item(
                Key={
                    HealthCheckTaskItem.FIELD_IDENTITY_ID: identity_id,
                    HealthCheckTaskItem.FIELD_TASK_ID: task_id
                },            
            )
        return response.get('Item', None)

    def create_new_healthcheck_task(self, identity_id, project_id, data_type):
        healthcheck_task_item = HealthCheckTaskItem.create_new_healthcheck_task(identity_id, project_id, data_type)
        self.insert_new_item(healthcheck_task_item)

        return healthcheck_task_item.task_id, healthcheck_task_item.process_type
    
    def get_status_of_task(self, identity_id, task_id):
        item = self._get_item(identity_id, task_id)
        if item is None:
            raise Exception(MESS_TASK_NOT_EXIST.format(task_id))
        else:
            return item[HealthCheckTaskItem.FIELD_STATUS]