import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.data_model import DataModel, DataItem
from models.healthcheck_info_model import HealthCheckInfoModel


class UpdateDBClass(LambdaBaseClass):
    
    KEY_DATA_TABLE_NAME = "data_table_name"

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore() 
        self.healcheck_model = HealthCheckInfoModel(os.environ["TABLE_HEALTHCHECK_INFO"]) 

    @LambdaBaseClass.parse_body
    def parser(self, body):
        
        self.logger.debug(f"body in main_parser: {body}")
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.healthcheck = body["healthcheck"]
        self.data_table_name = body[self.KEY_DATA_TABLE_NAME]        

    def _check_input_value(self):
        pass

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)   
        
        ### get data DB corresponding           
        self.data_model = DataModel(self.data_table_name)
            
        ### get all data that healthcheck_id does not exist
        healthcheck_id = self.healcheck_model.create_new_healthcheck_info(self.healthcheck, self.project_id)
        
        ### update healthcheck_id to data DB
        self.data_model.update_healthcheck_id(self.project_id, self.healthcheck["file_name"], healthcheck_id)
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    KEY_NAME_PROJECT_ID: self.project_id, 
                    "healthcheck_id":  healthcheck_id                  
                },
            is_in_stepfunction=True
        )
       

@error_response
def lambda_handler(event, context):

    return UpdateDBClass().handle(event, context)

    