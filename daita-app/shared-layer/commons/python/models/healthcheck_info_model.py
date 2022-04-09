from decimal import Decimal
import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List
from utils import create_unique_id, convert_current_date_to_iso8601


class HealthCheckInfoModel():
    
    FIELD_HC_INFO_ID        = "health_check_id"
    FIELD_PROJECT_ID        = "project_id"    
    
    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        
    def insert_new_item(self, item) -> None:
        response = self.table.put_item(
                Item = item                               
            ) 
        
        return

    def create_new_healthcheck_info(self, info, project_id):
        info_item = {
            self.FIELD_HC_INFO_ID: create_unique_id(),
            self.FIELD_PROJECT_ID: project_id, 
        }
        
        for key, value in info.items():
            if type(value) is float:
                value = Decimal(str(value))
            info_item[key] = value
            
        self.insert_new_item(info_item)

        return info_item[self.FIELD_HC_INFO_ID]