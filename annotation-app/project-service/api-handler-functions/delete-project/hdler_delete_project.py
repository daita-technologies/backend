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
from models.annotaition.anno_project_model import AnnoProjectModel
from models.annotaition.anno_data_model import AnnoDataModel
from models.annotaition.anno_project_sum_model import AnnoProjectSumModel


class DeleteProjectAnnotation(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.anno_project_model = AnnoProjectModel(self.env.TABLE_ANNO_PROJECT)
        self.model_data = AnnoDataModel(self.env.TABLE_ANNO_DATA_ORI)
        self.model_anno_prj_sum = AnnoProjectSumModel(self.env.TABLE_ANNO_PROJECT_SUMMARY)
        self.model_anno_deleted_prj = AnnoProjectModel(self.env.TABLE_ANNO_DELETED_PRJ)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_name = body["project_name"]
        self.project_id = body["project_id"]

    def handle(self, event, context):
        ### parse body
        self.parser(event)
        
        identity_id = self.get_identity(self.id_token, self.env.USER_POOL_ID, self.env.IDENTITY_POOL_ID)

        item_delete = self.anno_project_model.delete_project(identity_id, self.project_name)
        self.model_anno_deleted_prj.put_item_w_condition(item_delete)
        self.model_data.delete_project(self.project_id)
        self.model_anno_prj_sum.update_deleted_status(self.project_id, AnnoProjectSumModel.VALUE_TYPE_ORIGINAL)

        ### TODO delete in annotation
        ### delete category
        ### delete class
        ### delete label info
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={},
        )

def lambda_handler(event, context):
    return DeleteProjectAnnotation().handle(event=event,  context=context)