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
from models.project_model import ProjectModel, ProjectItem
from models.data_model import DataModel, DataItem
from models.annotaition.anno_data_model import AnnoDataModel


class DeleteProjectAnnotation(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.anno_project_model = AnnoProjectModel(self.env.TABLE_ANNO_PROJECT)
        self.model_data = AnnoDataModel(self.env.TABLE_ANNO_DATA_ORI)
    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_name = body["project_name"]
        self.project_id = body["project_id"]

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        
        identity_id = self.get_identity(self.id_token, self.env.USER_POOL_ID, self.env.IDENTITY_POOL_ID)
        self.anno_project_model.delete_project(identity_id,self.project_name)
        self.model_data.delete_project(self.project_id)
        return 