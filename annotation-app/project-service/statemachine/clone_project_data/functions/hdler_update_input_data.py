import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.annotaition.anno_data_model import AnnoDataModel
from models.annotaition.anno_project_sum_model import AnnoProjectSumModel
from models.annotaition.anno_project_model import AnnoProjectModel
from models.annotaition.anno_category_info import AnnoCategoryInfoModel
from models.annotaition.anno_class_info import AnnoClassInfoModel
from utils import get_bucket_key_from_s3_uri, split_ls_into_batch, convert_current_date_to_iso8601, create_unique_id


class MoveUpdateDataClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()  
        self.s3 = boto3.client('s3')

        self.anno_data_model = AnnoDataModel(self.env.TABLE_ANNO_DATA_ORI)
        self.anno_prj_sum_model = AnnoProjectSumModel(self.env.TABLE_ANNO_PROJECT_SUMMARY)
        self.anno_project_model = AnnoProjectModel(self.env.TABLE_ANNO_PROJECT)
        self.model_anno_category_info = AnnoCategoryInfoModel(self.env.TABLE_ANNO_CATEGORY_INFO)
        self.model_class_info = AnnoClassInfoModel(self.env.TABLE_ANNO_CLASS_INFO)
        self.model_ai_default_class = AnnoClassInfoModel(self.env.TABLE_ANNO_AI_DEFAULT_CLASS)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.identity_id = body[KEY_NAME_IDENTITY_ID]
        self.anno_project_id = body["anno_project_id"]
        self.s3_key_path = body["s3_key_path"]
        self.anno_project_name = body["anno_project_name"]
                   
    def _check_input_value(self):
        pass

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)   
        
        resultS3 = self.s3.get_object(Bucket=self.env.S3_ANNO_BUCKET_NAME, Key=self.s3_key_path)
        ls_info = json.loads(resultS3["Body"].read().decode())

        # update to DB
        # create the batch request from input data and summary the information
        ls_item_request = []
        total_size = 0
        count = 0
        for object in ls_info:
            # update summary information
            size_old = 0
            total_size += (object[2]-size_old)
            if size_old <= 0:
                count += 1

            type_method = VALUE_TYPE_DATA_ORIGINAL
            item_request = {
                AnnoDataModel.FIELD_PROJECT_ID: self.anno_project_id,  # partition key
                AnnoDataModel.FIELD_S3_KEY: object[1],          # sort_key
                AnnoDataModel.FIELD_FILE_ID: create_unique_id(),
                AnnoDataModel.FIELD_FILENAME: object[0],
                AnnoDataModel.FIELD_HASH: '',      # we use function get it mean that this field is optional in body
                AnnoDataModel.FIELD_SIZE: object[2],              # size must be in Byte unit
                AnnoDataModel.FIELD_IS_ORIGINAL:  True,
                AnnoDataModel.FIELD_CREATED_TIME: convert_current_date_to_iso8601()
            }
            ls_item_request.append(item_request)

        ### write data detail in to DB
        self.anno_data_model.batch_write(ls_item_request)

        ### update summary information
        self.anno_prj_sum_model.update_project_sum(self.anno_project_id, VALUE_TYPE_DATA_ORIGINAL, total_size, count, ls_item_request[0]['s3_key'], ls_item_request[0]['filename'])
        
        ### create default category
        category_id = self.model_anno_category_info.create_new_category(self.anno_project_id, "default", "this category was created by default")

        ### add default AI class to DB
        ls_default_items = self.model_ai_default_class.get_all_AI_default_class()
        self.model_class_info.add_default_AI_class(category_id, ls_default_items)

        # update generate status
        self.anno_project_model.update_project_gen_status_category_default(self.identity_id, self.anno_project_name, AnnoProjectModel.VALUE_GEN_STATUS_FINISH, category_id)

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={},
            is_in_stepfunction=True
        )
       
def lambda_handler(event, context):

    return MoveUpdateDataClass().handle(event, context)

    