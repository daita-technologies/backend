import os
import json

import boto3
from identity_check import *
from response import *
from error_messages import *
from lambda_base_class import LambdaBaseClass
from models.task_model import TaskModel


task_table = TaskModel(os.environ["TableDataFlowTaskName"], None)


class GetCompressDownloadClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.id_token = body["id_token"]
        self.task_id = body["task_id"]

    def handle(self, event, context):
        ### parse body
        self.parser(event)

        identity_id = self.get_identity(self.id_token)
        response = task_table.table.get_item(
            Key={"identity_id": identity_id, "task_id": self.task_id},
        )

        task = response.get("Item", None)
        # pop out identity_id if needed
        if task is None:
            raise Exception(MESS_TASK_NOT_EXIST.format(self.task_id))

        task.pop("identity_id", None)
        print("Task return: ", task)
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=task,
        )


@error_response
def lambda_handler(event, context):
    return GetCompressDownloadClass().handle(event, context)
