import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *

class GenerateTaskModel():
    FIELD_IDENTITY_ID = "identity_id"
    FIELD_PROJECT_ID = "project_id"
    FIELD_SATUS = "status"
    FIELD_NUM_VALUE = "num_value"

    def __init__(self) -> None:
        self.table = boto3.resource('dynamodb').Table(DB_GENERATE_TASK_TABLE_NAME)        
   
    def get_running_tasks(self, identity_id, project_id):
        response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                FilterExpression=Attr(self.FIELD_PROJECT_ID).eq(project_id) & 
                                Attr(self.FIELD_SATUS).ne(VALUE_GENERATE_TASK_STATUS_FINISH) & 
                                Attr(self.FIELD_SATUS).ne(VALUE_GENERATE_TASK_STATUS_ERROR)
            )
        return response.get("Items", [])