import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.task_model import TaskModel


class RIStatusClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.client_events = boto3.client("events")
        self.const = SystemParameterStore()
        self.task_model = TaskModel(os.environ["TABLE_REFERENCE_IMAGE_TASK"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.task_id = body[KEY_NAME_TASK_ID]

    def _get_task_status(self, identity_id, task_id):
        task_info = self.task_model.get_task_info_w_atribute(
            identity_id,
            task_id,
            ls_attribute=[
                TaskModel.FIELD_STATUS,
                TaskModel.FIELD_PROCESS_TYPE,
                TaskModel.FIELD_PROJECT_ID,
                TaskModel.FIELD_TASK_ID,
                TaskModel.FIELD_UPDATED_TIME,
            ],
        )
        return task_info

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### get status of task
        task_info = self._get_task_status(identity_id, self.task_id)

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=task_info,
        )


@error_response
def lambda_handler(event, context):

    return RIStatusClass().handle(event, context)
