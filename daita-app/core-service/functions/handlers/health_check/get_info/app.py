import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.healthcheck_info_model import HealthCheckInfoModel


class HCInfoClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.client_events = boto3.client("events")
        self.const = SystemParameterStore()
        self.health_check_model = HealthCheckInfoModel(
            os.environ["TABLE_HEALTHCHECK_INFO"]
        )

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.data_type = body[KEY_NAME_DATA_TYPE]

    def _check_input_value(self):
        if self.data_type not in [
            VALUE_TYPE_DATA_ORIGINAL,
            VALUE_TYPE_DATA_PREPROCESSED,
            VALUE_TYPE_DATA_AUGMENT,
        ]:
            raise Exception(
                MESS_DATA_TYPE_INPUT.format(
                    self.data_type,
                    [
                        VALUE_TYPE_DATA_ORIGINAL,
                        VALUE_TYPE_DATA_PREPROCESSED,
                        VALUE_TYPE_DATA_AUGMENT,
                    ],
                )
            )

        return

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### get list info
        items = self.health_check_model.get_info_project_w_data_type(
            self.project_id, self.data_type
        )

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=items,
        )


@error_response
def lambda_handler(event, context):

    return HCInfoClass().handle(event, context)
