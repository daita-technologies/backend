import boto3
import json
import os
import uuid

from config import *
from response import *
from error_messages import *
from utils import convert_current_date_to_iso8601, aws_get_identity_id, create_unique_id
import const


from lambda_base_class import LambdaBaseClass
from boto3.dynamodb.conditions import Key, Attr
from models.annotaition.anno_project_model import AnnoProjectModel
from models.annotaition.anno_label_info_model import AnnoLabelInfoModel



class CreateLabelCategoryClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')   
        self.label_info_model = AnnoLabelInfoModel(self.env.TABLE_ANNO_LABEL_INFO)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN] 
        self.file_id = body["file_id"]
        self.category_name = body["category_name"]
        self.category_des = body["category_des"]

    def _check_input_value(self): 
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### create category id indynamoDB
        category_id = create_unique_id()
        self.label_info_model.create_new_category(self.file_id, category_id, self.category_name, self.category_des)
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "category_id": category_id,
                    'category_name': self.category_name,
                    'category_des': self.category_des
                },
        )

@error_response
def lambda_handler(event, context):
    return CreateLabelCategoryClass().handle(event, context)