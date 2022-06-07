import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.reference_image_info_model import ReferenceImageInfoModel


class RIInfoClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.client_events = boto3.client("events")
        self.const = SystemParameterStore()
        self.refer_info_model = ReferenceImageInfoModel(
            os.environ["TABLE_REFERENCE_IMAGE_INFO"]
        )

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.project_id = body[KEY_NAME_PROJECT_ID]

    def _check_input_value(self):
        return

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### get list info
        items = self.refer_info_model.get_info_of_project(self.project_id)

        ### add filename to output
        for item in items:
            item["filename"] = item["image_s3_path"].split("/")[-1]

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=items,
        )


@error_response
def lambda_handler(event, context):

    return RIInfoClass().handle(event, context)
