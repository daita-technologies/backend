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
from models.annotaition.anno_class_info import AnnoClassInfoModel



class ListClassClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.model_class_info  = AnnoClassInfoModel(self.env.TABLE_ANNO_CLASS_INFO)
        

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN] 
        self.category_id = body["category_id"]

    def _check_input_value(self): 
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### add class name from list
        ls_items = self.model_class_info.query_all_class_of_category(self.category_id)
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "ls_class": ls_items
                },
        )

@error_response
def lambda_handler(event, context):
    return ListClassClass().handle(event, context)