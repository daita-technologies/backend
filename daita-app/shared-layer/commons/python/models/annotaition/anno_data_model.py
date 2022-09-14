import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List
from utils import convert_current_date_to_iso8601
from models.base_model import BaseModel

class AnnoDataModel(BaseModel):

    FIELD_PROJECT_ID        = "project_id"
    FIELD_FILENAME          = "filename"  
    FIELD_FILE_ID           = "file_id"  
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

    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        
    def _query_project_wo_healthcheck_id(self, project_id):
        response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                FilterExpression=Attr(self.FIELD_HEALTHCHECK_ID).not_exists()
            )
        items = response.get("Items", [])
        
        return items
    
    def _update_healthcheck_id(self, project_id, filename, healthcheck_id):
        response = self.table.update_item(
            Key={
                self.FIELD_PROJECT_ID: project_id,
                self.FIELD_FILENAME: filename,
            },
            ExpressionAttributeNames= {
                '#HC': self.FIELD_HEALTHCHECK_ID,
                '#UP_DATE': self.FIELD_UPDATE_TIME
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
        
        ls_s3_key = [(item[self.FIELD_FILENAME], item[self.FIELD_S3_KEY]) for item in items]
        
        return ls_s3_key

    def get_all_data_in_project(self, project_id):

        response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                ProjectionExpression=f"{self.FIELD_FILENAME}, {self.FIELD_S3_KEY}, {self.FIELD_SIZE}",
        )
        ls_items = response.get("Items", [])

        while 'LastEvaluatedKey' in response:
            next_token = response['LastEvaluatedKey']
            response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                ProjectionExpression=f"{self.FIELD_FILENAME}, {self.FIELD_S3_KEY}, {self.FIELD_SIZE}",
                ExclusiveStartKey=next_token
            )

            ls_items += response.get("Items", [])

        return [self.convert_decimal_indb_item(item) for item in ls_items]
    
    def update_healthcheck_id(self, project_id, filename, healthcheck_id):
        self._update_healthcheck_id(project_id, filename, healthcheck_id)

    def bad_write(self, ls_item_request):
        try:
            with self.table.batch_writer() as batch:
                for item in ls_item_request:
                    batch.put_item(Item=item)
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e))
        

    
        