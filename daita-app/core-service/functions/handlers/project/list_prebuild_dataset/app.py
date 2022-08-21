import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.prebuild_dataset_model import PrebuildDatasetModel


class ListPrebuildDatasetClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()   
        self.prebuild_dataset_model = PrebuildDatasetModel(os.environ["T_CONST_PREBUILD_DATASET"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]      

    def _check_input_value(self):        
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)
        
        ### get list info
        items = self.prebuild_dataset_model.get_list_prebuild_dataset()         
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=items,
        )

@error_response
def lambda_handler(event, context):

    return ListPrebuildDatasetClass().handle(event, context)

    