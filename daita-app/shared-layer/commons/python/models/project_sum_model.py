import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *


class ProjectSumModel():

    FIELD_IDENTITY_ID           = "identity_id"
    FIELD_PROJECT_ID            = "project_id"
    FIELD_TYPE                  = "type"


    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name)    

    def reset_prj_sum_preprocess(self, project_id, type_data):        
        response = self.table.update_item(
                                Key={
                                    self.FIELD_PROJECT_ID: project_id,
                                    self.FIELD_TYPE: type_data,
                                },
                                ExpressionAttributeNames= {
                                    '#CO': 'count',
                                    '#TS': 'total_size'
                                },
                                ExpressionAttributeValues = {
                                    ':ts':  0,
                                    ':co': 0
                                },
                                UpdateExpression = 'SET #TS = :ts, #CO = :co' 
                            )           
        return response
    
