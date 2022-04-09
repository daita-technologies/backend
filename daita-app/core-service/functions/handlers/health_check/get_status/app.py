import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.health_check_task_model import HealthCheckTaskModel

class HCStatusClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()   
        self.health_check_model = HealthCheckTaskModel(os.environ["TABLE_HEALTHCHECK_TASK"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.task_id = body[KEY_NAME_TASK_ID]    
        
    def _get_task_status(self, identity_id, task_id):
        status = self.health_check_model.get_status_of_task(identity_id, task_id)
        return status

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)  

        ### get status of task
        status = self._get_task_status(identity_id, self.task_id)        
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                KEY_NAME_TASK_STATUS: status,
            },
        )        

@error_response
def lambda_handler(event, context):

    return HCStatusClass().handle(event, context)

    