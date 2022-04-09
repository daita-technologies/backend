from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List
from utils import create_unique_id, convert_current_date_to_iso8601


class HealthCheckInfoModel():
    
    FIELD_HC_INFO_ID        = "healthcheck_id"
    FIELD_PROJECT_ID        = "project_id"
    FIELD_DATA_TYPE         = "data_type"  
    
    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        
    def insert_new_item(self, item) -> None:
        response = self.table.put_item(
                Item = item                               
            ) 
        return
    
    def _query_info_w_data_type(self, project_id, data_type):
        response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                FilterExpression=Attr(self.FIELD_DATA_TYPE).eq(data_type)
            )
        return response.get("Items", [])        

    def create_new_healthcheck_info(self, info, project_id, data_type):
        info_item = {
            self.FIELD_HC_INFO_ID: create_unique_id(),
            self.FIELD_PROJECT_ID: project_id, 
            self.FIELD_DATA_TYPE: data_type
        }
        
        for key, value in info.items():
            if type(value) is float:
                value = Decimal(str(value))
            info_item[key] = value
            
        self.insert_new_item(info_item)

        return info_item[self.FIELD_HC_INFO_ID]
    
    def get_info_project_w_data_type(self, project_id, data_type):
        items = self._query_info_w_data_type(project_id, data_type)
        for item in items:
            for key, value in item.items():
                if type(value) is Decimal:
                    if key in ["width", "height"]:
                        item[key] = int(value)
                    else:
                        item[key] = float(value)
                    
        return items        