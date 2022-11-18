from lambda_base_class import LambdaBaseClass
import json
import boto3
import hashlib
import hmac
import base64
import os
import uuid
from boto3.dynamodb.conditions import Key, Attr

from utils import convert_response, convert_current_date_to_iso8601, aws_get_identity_id, get_num_prj
import const
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


class CreateProject(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.id_token = body["id_token"]
        self.access_token = body["access_token"]
        self.project_name = body["project_name"]
        self.project_info = body.get("project_info", '')

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        try:
            identity_id = aws_get_identity_id(self.id_token, USERPOOLID, IDENTITY_POOL)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        db_resource=boto3.resource("dynamodb")

        try:
            # check length of projectname and project info
            if len(self.project_name) > const.MAX_LENGTH_PROJECT_NAME_INFO:
                raise Exception(const.MES_LENGTH_OF_PROJECT_NAME)
            if len(self.project_info) > const.MAX_LENGTH_PROJECT_DESCRIPTION:
                raise Exception(const.MES_LENGTH_OF_PROJECT_INFO)

            num_prj=get_num_prj(identity_id)
            if num_prj >= const.MAX_NUM_PRJ_PER_USER:
                raise Exception(const.MES_REACH_LIMIT_NUM_PRJ)

        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        _uuid=uuid.uuid4().hex
        project_id=f'{self.project_name}_{_uuid}'
        s3_prefix=f'{os.environ["BUCKET_NAME"]}/{identity_id}/{project_id}'
        db_client=boto3.client('dynamodb')
        try:
            is_sample=False
            gen_status="FINISH"
            table_prj=db_resource.Table(os.environ["TABLE_PROJECT"])
            table_prj.put_item(
                Item = {
                    'ID': _uuid,
                    'project_id': project_id,
                    'identity_id': identity_id,
                    'project_name': self.project_name,
                    's3_prefix': s3_prefix,
                    'project_info': self.project_info,
                    # 'sub': sub,
                    'created_date': convert_current_date_to_iso8601(),
                    'is_sample': is_sample,
                    'gen_status': gen_status
                },
                ConditionExpression = Attr('project_name').not_exists() & Attr(
                    'identity_id').not_exists()
            )

        except db_resource.meta.client.exceptions.ConditionalCheckFailedException as e:
            print('Error condition: ', e)
            err_mess=const.MES_DUPLICATE_PROJECT_NAME.format(
                self.project_name)
            return convert_response({"error": True,
                                    "success": False,
                                     "message": err_mess,
                                     "data": None})
        except Exception as e:
            print('Error: ', e)
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        return convert_response(
            {
                'data': {
                    "project_id": project_id,
                    "s3_prefix": s3_prefix,
                    "is_sample": is_sample,
                    "gen_status": gen_status,
                    "project_name": self.project_name
                },
                "error": False,
                "success": True,
                "message": None
            })


def lambda_handler(event, context):
    return CreateProject().handle(event = event, context = context)
