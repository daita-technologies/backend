import boto3
import json
import os
import uuid

from config import *
from response import *
from error_messages import *
from utils import convert_current_date_to_iso8601, aws_get_identity_id, get_num_prj
import const


from lambda_base_class import LambdaBaseClass
from boto3.dynamodb.conditions import Key, Attr
from models.annotaition.anno_project_model import AnnoProjectModel

MAX_NUMBER_LIMIT = 200

class ListProject(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.model_project = AnnoProjectModel(self.env.TABLE_ANNO_PROJECT)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN] 

    def _check_input_value(self): 
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token, self.env.USER_POOL_ID, self.env.IDENTITY_POOL_ID)

        ls_projects = self.model_project.get_all_project(identity_id)

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    'items': ls_projects
                },
        )


@error_response
def lambda_handler(event, context):

    return ListProject().handle(event, context)