

from typing import List
from lambda_base_class import LambdaBaseClass
import json
import boto3
import os

from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id, dydb_get_project_full, convert_current_date_to_iso8601
from error_messages import *

from models.annotaition.anno_project_sum_model import AnnoProjectSumModel
from models.annotaition.anno_data_model import AnnoDataModel
from response import *
import const


class ProjectUploadUpdateClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.model_data = AnnoDataModel(self.env.TABLE_ANNO_DATA_ORI)
        self.model_project_sum = AnnoProjectSumModel(self.env.TABLE_ANNO_PROJECT_SUMMARY)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_id = body["project_id"]
        self.ls_filename: List[str] = body["ls_filename"]
        
    def _check_input_value(self): 
        self.identity_id = self.get_identity(self.id_token, self.env.USER_POOL_ID, self.env.IDENTITY_POOL_ID)

        # check quantiy of items
        MAX_NUMBER_ITEM_QUERY = 200
        if len(self.ls_filename) > MAX_NUMBER_ITEM_QUERY:
            raise Exception(
                f'The number of items is over {MAX_NUMBER_ITEM_QUERY}')
        

    def handle(self, event, context):
        ### parse body
        self.parser(event)

        # query data from DB
        ls_data = self.model_data.get_item_from_list(self.project_id, self.ls_filename)
        
        # check available image is over the limitation
        current_num_data = self.model_project_sum.get_current_number_data_in_prj(self.project_id)
        if len(self.ls_filename)-len(ls_data)+current_num_data > const.MAX_NUM_IMAGES_IN_ORIGINAL:
            raise (Exception(
                f'The number of images should not exceed {const.MAX_NUM_IMAGES_IN_ORIGINAL}!'))

        return convert_response({
            'data': ls_data,
            "error": False,
            "success": True,
            "message": None
        })

@error_response
def lambda_handler(event, context):
    return ProjectUploadUpdateClass().handle(event=event,  context=context)