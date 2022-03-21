
import json

from config import *
from response import *
from error_messages import *

from lambda_base_class import LambdaBaseClass
from system_parameter_store import SystemParameterStore
from models.generate_task_model import GenerateTaskModel

class TaskProgressClass(LambdaBaseClass):

    def __init__(self) -> None:
        super().__init__()
        self.const = SystemParameterStore()   
        self.generate_task_model = GenerateTaskModel()    

    def _get_task_info(self, generate_task_model: GenerateTaskModel, identity_id: str, task_id: str):
        item = generate_task_model.get_task_info(identity_id, task_id)
        if item is None:
            raise(Exception(MESS_TASK_NOT_EXIST.format(task_id)))                    
        self.logger.debug(f"item response: {item}")

        return item

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.task_id = body[KEY_NAME_TASK_ID]

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)       

        ### get task info, if task not exist, raise exception       
        item = self._get_task_info(self.generate_task_model, identity_id, self.task_id)      
                
        return generate_response(
            message="OK",
            status_code = HTTPStatus.OK,
            data = item.to_dict(),
        )

@error_response
def lambda_handler(event, context):

    return TaskProgressClass().handle(event, context)

    