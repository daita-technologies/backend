import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List
from utils import convert_current_date_to_iso8601

class DataItem():
    
    FIELD_PROJECT_ID        = "project_id"
    FIELD_FILENAME          = "filename"    
    FIELD_CREATE_TIME       = "created_time"
    FIELD_UPDATE_TIME       = "updated_time"
    FIELD_GEN_ID            = "gen_id"
    FIELD_HASH              = "hash"    
    FIELD_IS_ORIGINAL       = "is_ori"
    FIELD_S3_KEY            = "s3_key"
    FIELD_TYPE_METHOD       = "type_method"
    FIELD_SIZE              = "size"
    FIELD_HEALTHCHECK_ID    = "healthcheck_id"      

    REQUEST_TYPE_ALL    = "all"

    def __init__(self) -> None:   
        self.project_id = ""
        self.filename = ""  
        self.gen_id = ""
        self.hash = ""
        self.is_original = False
        self.s3_key = ""
        self.type_method = ""
        self.size = 0
        self.healthcheck_id = None
        self.create_time    = convert_current_date_to_iso8601()
        self.updated_time   = convert_current_date_to_iso8601()

    @classmethod
    def from_db_item(cls, item_info):
        if item_info is None:
            return None
        else:
            object = cls()
            object.item_db = item_info
            
            object.project_id = item_info.get(object.FIELD_PROJECT_ID)

            object.method_id          = item_info.get(object.FIELD_METHOD_ID)
            object.method_name        = item_info.get(object.FIELD_METHOD_NAME)       

            return object
        
    def to_dict(self, request = REQUEST_TYPE_ALL):
        print(self.__dict__)
        if request == self.REQUEST_TYPE_ALL:
            dict_info = {
                self.FIELD_PROJECT_ID: self.project_id,  
                self.FIELD_FILENAME: self.filename,
                self.GEN_ID: self.gen_id,
                self.FIELD_HASH: self.hash,
                self.FIELD_IS_ORIGINAL: self.is_original,
                self.FIELD_S3_KEY: self.s3_key,
                self.FIELD_SIZE: self.size,
                self.FIELD_TYPE_METHOD: self.type_method,        
                self.FIELD_CREATE_TIME: self.create_time,
                self.FIELD_UPDATE_TIME: self.updated_time
            }
        return dict_info


class DataModel():
    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        
    def _query_project_wo_healthcheck_id(self, project_id):
        response = self.table.query (
                KeyConditionExpression=Key(DataItem.FIELD_PROJECT_ID).eq(project_id),
                FilterExpression=Attr(DataItem.FIELD_HEALTHCHECK_ID).not_exists()
            )
        items = response.get("Items", [])
        
        return items
    
    def _update_healthcheck_id(self, project_id, filename, healthcheck_id):
        response = self.table.update_item(
            Key={
                DataItem.FIELD_PROJECT_ID: project_id,
                DataItem.FIELD_FILENAME: filename,
            },
            ExpressionAttributeNames= {
                '#HC': DataItem.FIELD_HEALTHCHECK_ID,
                '#UP_DATE': DataItem.FIELD_UPDATE_TIME
            },
            ExpressionAttributeValues = {
                ':hc':  healthcheck_id,
                ':da': convert_current_date_to_iso8601(),                
            },
            UpdateExpression = 'SET #HC = :hc , #UP_DATE = :da'
        )
        return
        
    def get_all_wo_healthcheck_id(self, project_id: str):
        """
        get all data that does not have healthcheck_id
        Args:
            project_id (str): project id

        Returns:
            _type_: _description_
        """
        
        items = self._query_project_wo_healthcheck_id(project_id)
        
        ls_s3_key = [(item[DataItem.FIELD_FILENAME], item[DataItem.FIELD_S3_KEY]) for item in items]
        
        return ls_s3_key

    def get_all_data_in_project(self, project_id):
        response = self.table.query (
                KeyConditionExpression=Key(DataItem.FIELD_PROJECT_ID).eq(project_id),
                ProjectionExpression=f"{DataItem.FIELD_FILENAME}, {DataItem.FIELD_S3_KEY}",
            )
        items = response.get("Items", [])

        return items
    
    def update_healthcheck_id(self, project_id, filename, healthcheck_id):
        self._update_healthcheck_id(project_id, filename, healthcheck_id)
        

    
        