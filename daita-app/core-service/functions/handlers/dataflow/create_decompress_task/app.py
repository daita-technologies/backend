import os
import json
import uuid
from datetime import datetime

import boto3
from response import *
from error_messages import *
from identity_check import *
from utils import create_unique_id, convert_current_date_to_iso8601, create_task_id_w_created_time
from models.task_model import TaskModel

from lambda_base_class import LambdaBaseClass


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")
PROJECTS_TABLE = os.getenv("ProjectsTable")

stepfunctions = boto3.client('stepfunctions')
db = boto3.resource('dynamodb')
task_table = db.Table(DECOMPRESS_TASK_TABLE)
projects_table = db.Table(PROJECTS_TABLE)

class CreateDecompressClass(LambdaBaseClass):

    def __init__(self) -> None:
        super().__init__()



    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.file_url = body["file_url"]
        self.id_token = body["id_token"]
        self.project_id = body['project_id']
        self.project_name = body['project_name']
        self.type_method = body.get('type_method', 'ORIGINAL')

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        task_id = create_task_id_w_created_time()
        response = task_table.put_item(
            Item={
                TaskModel.FIELD_IDENTITY_ID: identity_id,
                TaskModel.FIELD_TASK_ID: task_id,
                "file_url": self.file_url,
                TaskModel.FIELD_STATUS: VALUE_TASK_RUNNING,
                TaskModel.FIELD_CREATE_TIME: convert_current_date_to_iso8601(),
                TaskModel.FIELD_UPDATED_TIME: convert_current_date_to_iso8601(),
                TaskModel.FIELD_PROJECT_ID: self.project_id,
                TaskModel.FIELD_PROCESS_TYPE: VALUE_PROCESS_TYPE_UPLOAD
            }
        )

        response = projects_table.get_item(
            Key={
                "identity_id": identity_id,
                "project_name": self.project_name
            },
            ProjectionExpression="s3_prefix"
        )
        print(response)
        s3_prefix = response["Item"].get("s3_prefix")

        stepfunction_input = {
            "file_url": self.file_url,
            "task_id": task_id,
            "id_token": self.id_token,
            "project_id": self.project_id,
            "project_name": self.project_name,
            "type_method": self.type_method,
            "s3_prefix": s3_prefix,
            "identity_id": identity_id
        }
        response = stepfunctions.start_execution(
            stateMachineArn=os.getenv("DecompressFileStateMachineArn"),
            input=json.dumps(stepfunction_input)
        )

        return generate_response(
                message="OK",
                status_code=HTTPStatus.OK,
                data= {
                    "task_id": task_id,
                    "file_url": self.file_url,
                },
            )


@error_response
def lambda_handler(event, context):

    return CreateDecompressClass().handle(event, context)
