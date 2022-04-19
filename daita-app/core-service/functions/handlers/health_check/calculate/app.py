import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.health_check_task_model import HealthCheckTaskModel, HealthCheckTaskItem


class HealthCheckClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()   
        self.health_check_model = HealthCheckTaskModel(os.environ["TABLE_HEALTHCHECK_TASK"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.data_type = body[KEY_NAME_DATA_TYPE] 

    def _check_input_value(self):
        if self.data_type not in [VALUE_TYPE_DATA_ORIGINAL, VALUE_TYPE_DATA_PREPROCESSED, VALUE_TYPE_DATA_AUGMENT]:
            raise Exception(MESS_DATA_TYPE_INPUT.format(self.data_type, [VALUE_TYPE_DATA_ORIGINAL, VALUE_TYPE_DATA_PREPROCESSED, VALUE_TYPE_DATA_AUGMENT]))

        return

    def _create_task(self, identity_id, project_id, data_type):
        # create task id
        task_id, process_type = self.health_check_model.create_new_healthcheck_task(identity_id, project_id, data_type)
        return task_id, process_type 
      
    def _put_event_bus(self, detail_pass_para):        

        response = self.client_events.put_events(
                        Entries=[
                            {
                                'Source': 'source.events',
                                'DetailType': 'lambda.event',
                                'Detail': json.dumps(detail_pass_para),
                                'EventBusName': os.environ["EVENT_BUS_NAME"]
                            },
                        ]
                    )
        entries = response["Entries"]

        return entries[0]["EventId"]     

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)  

        ### create taskID and update to DB
        task_id, process_type = self._create_task(identity_id, self.project_id, self.data_type)

        ### push event to eventbridge
        detail_pass_para = {
            KEY_NAME_IDENTITY_ID: identity_id,
            KEY_NAME_PROJECT_ID: self.project_id,            
            KEY_NAME_DATA_TYPE: self.data_type,           
            KEY_NAME_TASK_ID: task_id
        }
        event_id = self._put_event_bus(detail_pass_para) 
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                KEY_NAME_TASK_ID: task_id,
                KEY_NAME_PROCESS_TYPE: process_type
            },
        )

        

@error_response
def lambda_handler(event, context):

    return HealthCheckClass().handle(event, context)

    