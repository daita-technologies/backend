import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.data_model import DataModel, DataItem


class GetDataClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.client_events = boto3.client("events")
        self.const = SystemParameterStore()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.identity_id = body[KEY_NAME_IDENTITY_ID]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.data_type = body[KEY_NAME_DATA_TYPE]
        self.task_id = body[KEY_NAME_TASK_ID]

    def _check_input_value(self):
        pass

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### get data DB corresponding
        if self.data_type == VALUE_TYPE_DATA_ORIGINAL:
            data_table_name = os.environ["TABLE_DATA_ORIGINAL"]
        elif self.data_type == VALUE_TYPE_DATA_AUGMENT:
            data_table_name = os.environ["TABLE_DATA_AUGMENT"]
        elif self.data_type == VALUE_TYPE_DATA_PREPROCESSED:
            data_table_name = os.environ["TABLE_DATA_PREPROCESS"]
        self.data_model = DataModel(data_table_name)

        ### get all data that healthcheck_id does not exist
        ls_info = self.data_model.get_all_wo_healthcheck_id(self.project_id)

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={"data_table_name": data_table_name, "ls_file_s3": ls_info},
            is_in_stepfunction=True,
        )


def lambda_handler(event, context):

    return GetDataClass().handle(event, context)
