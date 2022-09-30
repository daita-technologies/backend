

from lambda_base_class import LambdaBaseClass
import json
import boto3
import os

from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id, dydb_get_project_full
from error_messages import *

from models.annotaition.anno_project_model import AnnoProjectModel
from models.annotaition.anno_project_sum_model import AnnoProjectSumModel


class GetProjectInfoClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.anno_project_model = AnnoProjectModel(self.env.TABLE_ANNO_PROJECT)
        self.anno_project_sum_model = AnnoProjectSumModel(self.env.TABLE_ANNO_PROJECT_SUMMARY)

    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_name = body["project_name"]

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        
        identity_id = self.get_identity(self.id_token, self.env.USER_POOL_ID, self.env.IDENTITY_POOL_ID)

        ### get project_id
        project_info = self.anno_project_model.get_project_info(identity_id, self.project_name, 
                                                                [AnnoProjectModel.FIELD_PROJECT_ID, AnnoProjectModel.FIELD_CATEGORY_DEFAULT, AnnoProjectModel.FIELD_S3_PREFIX,
                                                                AnnoProjectModel.FIELD_S3_LABEL])
        if project_info is None:
            raise Exception(MESS_PROJECT_NOT_EXIST.format(self.project_name))
        project_id = project_info[AnnoProjectModel.FIELD_PROJECT_ID]
        
        # get info detail of a project
        items = self.anno_project_sum_model.query_data_project_id(project_id)
        if len(items)>0:
            groups = {}
            for item in items:
                type = item['type']
                groups[type] = {
                    'count': int(item['count']),
                    'size': int(item['total_size'])                
                }
        else:
            groups = None

        return convert_response({'data': {
                                        "identity_id": identity_id,
                                        "project_name": self.project_name,
                                        "project_id": project_id,
                                        "s3_raw_data": project_info[AnnoProjectModel.FIELD_S3_PREFIX],
                                        "s3_label": project_info[AnnoProjectModel.FIELD_S3_LABEL],
                                        "default_category_id": project_info[AnnoProjectModel.FIELD_CATEGORY_DEFAULT],
                                        "groups": groups,
                                    },
                                "error": False,
                                "success": True,
                                "message": None })


def lambda_handler(event, context):
    return GetProjectInfoClass().handle(event=event,  context=context)