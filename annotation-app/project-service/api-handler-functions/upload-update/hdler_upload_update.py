

from lambda_base_class import LambdaBaseClass
import json
import boto3
import os

from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id, dydb_get_project_full, convert_current_date_to_iso8601
from error_messages import *
from response import *

from models.annotaition.anno_project_sum_model import AnnoProjectSumModel
from models.annotaition.anno_data_model import AnnoDataModel



class ProjectUploadUpdateClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.model_data = AnnoDataModel(self.env.TABLE_ANNO_DATA_ORI)
        self.model_project_sum = AnnoProjectSumModel(self.env.TABLE_ANNO_PROJECT_SUMMARY)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_id = body['project_id']
        self.project_name = body['project_name']
        self.ls_object_info = body['ls_object_info']
        
    def _check_input_value(self): 
        self.identity_id = self.get_identity(self.id_token, self.env.USER_POOL_ID, self.env.IDENTITY_POOL_ID)

        # check quantiy of items
        MAX_NUMBER_ITEM_PUT = 200
        if len(self.ls_object_info) > MAX_NUMBER_ITEM_PUT:
            raise Exception(
                f'The number of items is over {MAX_NUMBER_ITEM_PUT}')
        if len(self.ls_object_info) == 0:
            raise Exception('The number of items must not empty')

    def handle(self, event, context):
        ### parse body
        self.parser(event)

        ### update summary information
        total_size = 0
        count = 0
        for object in self.ls_object_info:
            size_old = object.get('size_old', 0)
            total_size += (object['size']-size_old)
            if size_old <= 0:
                count += 1
            
        ### check number images in original must smaller than a limitation
        item = self.model_project_sum.get_item_prj_sum_info(self.project_id, ls_fields_projection=[])
        if item:
            current_num_data = item.get(AnnoProjectSumModel.FIELD_NUM_EXIST_DATA, 0)
            thumbnail_key = item.get(AnnoProjectSumModel.FIELD_THUM_KEY, None)
            thumbnail_filename = item.get(AnnoProjectSumModel.FIELD_THUM_FILENAME, None)
        else:
            current_num_data = 0
            thumbnail_key = self.ls_object_info[0]["s3_key"]
            thumbnail_filename = self.ls_object_info[0]["filename"]

        num_final = current_num_data + len(self.ls_object_info)
        
        ### put item from ls object
        self.model_data.put_item_from_ls_object(self.project_id, self.ls_object_info)

        ### update summary information
        self.model_project_sum.update_upload_new_data(self.project_id, total_size=total_size, count = count, num_final=num_final,
                                                        thum_filename=thumbnail_filename, thum_s3_key=thumbnail_key)

        return convert_response({'data': {},
                                "error": False,
                                 "success": True,
                                 "message": None})

@error_response
def lambda_handler(event, context):
    return ProjectUploadUpdateClass().handle(event=event,  context=context)