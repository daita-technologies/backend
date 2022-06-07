import os
import json
import uuid
from datetime import datetime

import boto3

from response import *
from error_messages import *
from identity_check import *
from utils import create_task_id_w_created_time, convert_current_date_to_iso8601
from lambda_base_class import LambdaBaseClass
from models.task_model import TaskModel


task_table = TaskModel(os.environ["TableDataFlowTaskName"], None)
COMPRESS_DOWNLOAD_STATEMACHINE = os.getenv("CompressDownloadStateMachineArn")

stepfunctions = boto3.client("stepfunctions")


class CreateCompressDownloadClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body["id_token"]
        self.down_type = body["down_type"]
        self.project_id = body["project_id"]
        self.project_name = body["project_name"]

    def handle(self, event, context):
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        task_id = create_task_id_w_created_time()
        response = task_table.update_attribute(
            task_id=task_id,
            identity_id=identity_id,
            ls_update=[
                ("down_type", self.down_type),
                (KEY_NAME_TASK_STATUS, VALUE_TASK_RUNNING),
                (KEY_NAME_CREATED_TIME, convert_current_date_to_iso8601()),
                ("updated_at", convert_current_date_to_iso8601()),
                ("project_id", self.project_id),
                ("project_name", self.project_name),
                (KEY_NAME_PROCESS_TYPE, VALUE_PROCESS_TYPE_DOWNLOAD),
            ],
        )

        stepfunction_input = {
            "task_id": task_id,
            "identity_id": identity_id,
            "down_type": self.down_type,
            "id_token": self.id_token,
            "project_id": self.project_id,
            "project_name": self.project_name,
        }
        response = stepfunctions.start_execution(
            stateMachineArn=COMPRESS_DOWNLOAD_STATEMACHINE,
            input=json.dumps(stepfunction_input),
        )

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                "task_id": task_id,
            },
        )


@error_response
def lambda_handler(event, context):
    return CreateCompressDownloadClass().handle(event, context)
