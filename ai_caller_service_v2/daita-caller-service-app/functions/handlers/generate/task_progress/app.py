
import json

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from models.generate_task_model import GenerateTaskModel

import logging



class TaskProgressClass():

    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(os.environ["LOGGING"])    
        self.const = SystemParameterStore()   
        self.generate_task_model = GenerateTaskModel()

    def _parse_body(self, event):
        ### parse parameter from body input   
        try:    
            body = json.loads(event['body'])
            self.logger.info("Body: {}".format(body))

            self.id_token = body[KEY_NAME_ID_TOKEN]
            self.task_id = body[KEY_NAME_TASK_ID]
        except Exception as e:
            raise Exception(MESS_INVALID_JSON_INPUT) from e

        ### check input value
        self._check_input_value()
        
        return

    def _get_identity(self, id_token):
        identity = aws_get_identity_id(id_token)
        self.logger.info(f"identity: {identity}")
        return identity

    def _check_input_value(self):        
        pass
        return

    def _get_task_info(self, generate_task_model: GenerateTaskModel, identity_id: str, task_id: str):
        item = generate_task_model.get_task_info(identity_id, task_id)
        if item is None:
            raise(Exception(MESS_TASK_NOT_EXIST.format(task_id)))                    
        self.logger.debug(f"item response: {item}")

        return item

    def process_event(self, event, context):
        
        ### parse body
        self._parse_body(event)

        ### check identity
        identity_id = self._get_identity(self.id_token)       

        ### get task info, if task not exist, raise exception       
        item = self._get_task_info(self.generate_task_model, identity_id, self.task_id)      
                
        return generate_response(
            message="OK",
            status_code = HTTPStatus.OK,
            data = item.to_dict(),
        )

@error_response
def lambda_handler(event, context):

    return TaskProgressClass().process_event(event, context)

    