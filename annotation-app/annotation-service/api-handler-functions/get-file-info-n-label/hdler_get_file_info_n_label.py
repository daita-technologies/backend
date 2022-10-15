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
from models.annotaition.anno_data_model import AnnoDataModel
from models.annotaition.anno_label_info_model import AnnoLabelInfoModel


class GetFileInfoClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.model_data = AnnoDataModel(self.env.TABLE_ANNO_DATA_ORI)
        self.model_label_info = AnnoLabelInfoModel(self.env.TABLE_ANNO_LABEL_INFO)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN] 
        self.project_id = body["project_id"]
        self.file_name = body["filename"]
        self.category_id = body.get("category_id", "")

    def _check_input_value(self): 
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token, self.env.USER_POOL_ID, self.env.IDENTITY_POOL_ID)

        ### get file info including link to s3 of segmentation prelabel
        file_info = self.model_data.get_item(self.project_id, self.file_name)
        file_id = file_info[AnnoDataModel.FIELD_FILE_ID]

        ### get label json info: label with category and  json label
        if len(self.category_id)==0:
            label_info = self.model_label_info.query_all_category_label(file_id)
        else:
            label_info = self.model_label_info.get_label_info_of_category(file_id, self.category_id)
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "file_info": file_info,
                    "label_info": label_info
                },
        )

@error_response
def lambda_handler(event, context):

    return GetFileInfoClass().handle(event, context)