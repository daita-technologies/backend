import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *

FIELD_IDENTITY_ID   = "identity_id"
FIELD_PROJECT_ID    = "project_id"
FIELD_PROJECT_NAME  = "project_name"
FIELD_GEN_STATUS    = "gen_status"
FIELD_S3_PREFIX     = "s3_prefix"
FIELD_IS_SAMPLE     = "is_sample"
FIELD_PROJECT_INFO  = "project_info"
FIELD_TIMES_AUGMENT = "times_generated"
FIELD_TIMES_PREPRO  = "times_propr"

class ProjectRecord():

    def __init__(self, dict_info) -> None:
        pass

class ProjectModel():
    


    def __init__(self) -> None:
        self.table = boto3.resource('dynamodb').Table(DB_PROJECT_TABLE_NAME)               
   
    def get_project_info(self, identity_id, project_name):            
        response = self.table.get_item(
            Key={
                self.FIELD_IDENTITY_ID: identity_id,
                self.FIELD_PROJECT_NAME: project_name,
            },
            ProjectionExpression= f'{self.FIELD_PROJECT_ID}, {self.FIELD_S3_PREFIX}, {self.FIELD_TIMES_AUGMENT}, {self.FIELD_TIMES_PREPRO}'
        )
        
        return response.get('Item', None)
