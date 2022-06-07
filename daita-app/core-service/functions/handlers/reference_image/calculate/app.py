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


class ReferenceImageClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.client_events = boto3.client("events")
        self.const = SystemParameterStore()
        self.task_model = TaskModel(os.environ["TABLE_REFERENCE_IMAGE_TASK"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.project_name = body.get(KEY_NAME_PROJECT_NAME, "")
        self.ls_method_id = LS_METHOD_ID_SUPPORT_REFERENCE_IMG
        self.ls_method_client_choose = body.get(KEY_NAME_LS_METHOD_CHOOSE, {})

    def _check_input_value(self):
        return

    def _create_task(
        self,
        identity_id,
        project_id,
        project_name,
        ls_method_id,
        ls_method_client_choose,
    ):
        # create task id
        task_id, process_type = self.task_model.create_task_reference_image(
            identity_id, project_id, project_name, ls_method_id, ls_method_client_choose
        )
        return task_id, process_type

    def _put_event_bus(self, detail_pass_para):

        response = self.client_events.put_events(
            Entries=[
                {
                    "Source": "source.events",
                    "DetailType": "lambda.event",
                    "Detail": json.dumps(detail_pass_para),
                    "EventBusName": os.environ["EVENT_BUS_NAME"],
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
        task_id, process_type = self._create_task(
            identity_id,
            self.project_id,
            self.project_name,
            self.ls_method_id,
            self.ls_method_client_choose,
        )

        ### push event to eventbridge
        detail_pass_para = {
            KEY_NAME_IDENTITY_ID: identity_id,
            KEY_NAME_PROJECT_ID: self.project_id,
            KEY_NAME_LS_METHOD_ID: self.ls_method_id,
            KEY_NAME_TASK_ID: task_id,
            KEY_NAME_PROJECT_NAME: self.project_name,
            KEY_NAME_LS_METHOD_CHOOSE: self.ls_method_client_choose,
        }
        event_id = self._put_event_bus(detail_pass_para)

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={KEY_NAME_TASK_ID: task_id, KEY_NAME_PROCESS_TYPE: process_type},
        )


@error_response
def lambda_handler(event, context):

    return ReferenceImageClass().handle(event, context)
