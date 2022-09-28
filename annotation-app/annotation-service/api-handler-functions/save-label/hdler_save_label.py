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
from models.annotaition.anno_label_info_model import AnnoLabelInfoModel



class SaveLabelClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')   
        self.model_label_info = AnnoLabelInfoModel(self.env.TABLE_ANNO_LABEL_INFO)
        

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN] 
        self.dict_s3_key_label = body["dict_s3_key"]  ### contain category_id and s3_key_label
        self.file_id = body["file_id"]

    def _check_input_value(self): 
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token, self.env.USER_POOL_ID, self.env.IDENTITY_POOL_ID)

        ### update label info for each category of file
        for category_id, s3_key_json_label in self.dict_s3_key_label.items():
            self.model_label_info.update_label_for_category(self.file_id, category_id, s3_key_json_label)
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={},
        )

@error_response
def lambda_handler(event, context):

    return SaveLabelClass().handle(event, context)