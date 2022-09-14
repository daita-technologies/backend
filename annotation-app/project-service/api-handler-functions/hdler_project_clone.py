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


class ProjectCloneClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')   
        self.client_step_func = boto3.client('stepfunctions')
        self.anno_project_model = AnnoProjectModel(self.env.TABLE_ANNO_PROJECT)
        self.daita_project_model = ProjectModel(self.env.TABLE_DAITA_PROJECT)
        

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN] 
        self.anno_project_name = body["anno_project_name"]
        self.daita_project_name = body["daita_project_name"]
        self.project_info = body["project_info"]

    def _check_input_value(self): 
        # ### check number max
        # if self.number_random <= 0 or self.number_random >= prebuild_dataset[PrebuildDatasetModel.FIELD_TOTAL_IMAGES]:
        #     self.number_random = prebuild_dataset[PrebuildDatasetModel.FIELD_TOTAL_IMAGES]

        # ### udpate the link to s3
        # self.s3_key = prebuild_dataset[PrebuildDatasetModel.FIELD_S3_KEY]
        # self.visual_name = prebuild_dataset[PrebuildDatasetModel.FIELD_VISUAL_NAME]

        ###
        try:
            # check length of projectname and project info
            if len(self.anno_project_name) > const.MAX_LENGTH_PROJECT_NAME_INFO:
                raise Exception(const.MES_LENGTH_OF_PROJECT_NAME)
            # if len(self.project_info) > const.MAX_LENGTH_PROJECT_NAME_INFO:
            #     raise Exception(const.MES_LENGTH_OF_PROJECT_INFO)
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e))
                 
        return        

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### check daita_project exist or not
        project_rec = self.daita_project_model.get_project_info(identity_id, self.daita_project_name)
        if project_rec is None:
            raise Exception(MESS_PROJECT_NOT_EXIST.format(self.daita_project_name))

        ### check limit project
        # num_prj=get_num_prj(identity_id)
        # if num_prj >= const.MAX_NUM_PRJ_PER_USER:
        #     raise Exception(const.MES_REACH_LIMIT_NUM_PRJ)

        ### create project on DB
        _uuid = uuid.uuid4().hex
        project_id = f'{self.anno_project_name}_{_uuid}'
        s3_prj_root = f'{self.env.S3_ANNO_BUCKET_NAME}/{identity_id}/{project_id}'
        s3_prefix = f'{self.env.S3_ANNO_BUCKET_NAME}/{identity_id}/{project_id}/{const.FOLDER_RAW_DATA_NAME}'
        db_resource = boto3.resource('dynamodb')
        try:
            gen_status = AnnoProjectModel.VALUE_GEN_STATUS_GENERATING
            item = {
                        AnnoProjectModel.FIELD_PROJECT_ID: project_id,
                        AnnoProjectModel.FIELD_IDENTITY_ID: identity_id,
                        AnnoProjectModel.FIELD_PROJECT_NAME: self.anno_project_name,
                        AnnoProjectModel.FIELD_S3_PREFIX: s3_prefix,
                        AnnoProjectModel.FIELD_S3_PRJ_ROOT: s3_prj_root,
                        AnnoProjectModel.FIELD_PROJECT_INFO: self.project_info,
                        AnnoProjectModel.FIELD_CREATED_DATE: convert_current_date_to_iso8601(),
                        AnnoProjectModel.FIELD_GEN_STATUS: gen_status,
                        AnnoProjectModel.FIELD_LINKED_PROJECT: project_rec.get_value_w_default(ProjectItem.FIELD_PROJECT_ID, "")
                    }
            condition = Attr(AnnoProjectModel.FIELD_PROJECT_NAME).not_exists() & Attr(AnnoProjectModel.FIELD_IDENTITY_ID).not_exists()
            self.anno_project_model.put_item_w_condition(item, condition=condition)
        except db_resource.meta.client.exceptions.ConditionalCheckFailedException as e:
            print('Error condition: ', e)
            raise Exception(MES_DUPLICATE_PROJECT_NAME.format(self.project_name))
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e)) 
        
        ### call async step function
        stepfunction_input = {
            "identity_id": identity_id,
            "anno_project_id": project_id,
            "anno_project_name": self.anno_project_name,
            "anno_bucket_name": self.env.S3_ANNO_BUCKET_NAME,
            "daita_project_id": project_rec.get_value_w_default(ProjectItem.FIELD_PROJECT_ID, ""),
            "s3_prefix_create": s3_prefix,
            # "s3_prefix_prebuild": self.s3_key if (f"s3://{self.bucket_name}" not in self.s3_key) else self.s3_key.replace(f"s3://{self.bucket_name}/", "")
        }
        response = self.client_step_func.start_execution(
            stateMachineArn=self.env.SM_CLONE_PROJECT_ARN,
            input=json.dumps(stepfunction_input)
        )        
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "project_id": project_id,
                    "s3_prefix": s3_prefix,
                    "s3_prj_root": s3_prj_root,
                    "gen_status": gen_status,
                    "project_name": self.anno_project_name,
                    "link_daita_prj_id": project_rec.get_value_w_default(ProjectItem.FIELD_PROJECT_ID)
                },
        )

@error_response
def lambda_handler(event, context):

    return ProjectCloneClass().handle(event, context)