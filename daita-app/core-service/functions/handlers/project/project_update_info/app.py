from lambda_base_class import LambdaBaseClass
import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id, dydb_get_project_id, dydb_get_project_full
import const


def lambda_handler(event, context):
    return ProjectUpdateCls().handle(event,context)


class ProjectUpdateCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_name = body["cur_project_name"]
        self.new_prj_name = body.get("new_project_name", '')
        self.new_description = body.get("new_description", '')
        if self.project_name == self.new_prj_name:
            raise Exception(const.MES_PROJECT_SAME.format(self.new_prj_name))

        # check length of projectname and project info
        if len(self.new_prj_name) > const.MAX_LENGTH_PROJECT_NAME_INFO:
            raise Exception(const.MES_LENGTH_OF_PROJECT_NAME)
        if len(self.new_description) > const.MAX_LENGTH_PROJECT_NAME_INFO:
            raise Exception(const.MES_LENGTH_OF_PROJECT_INFO)

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        try:
            identity_id = aws_get_identity_id(self.id_token)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        db_resource = boto3.resource('dynamodb')
        # get project_id
        try:
            table = db_resource.Table(os.environ['T_PROJECT'])
            res_project = table.get_item(
                Key={
                    'identity_id': identity_id,
                    'project_name': self.project_name
                }
            )
            if res_project.get('Item', None):
                current_info = res_project['Item']
                if len(new_description) == 0:
                    new_description = current_info['project_info']

                if len(self.new_prj_name) > 0:
                    # check new name exist or not
                    response = table.get_item(
                        Key={
                            'identity_id': identity_id,
                            'project_name': self.new_prj_name
                        }
                    )
                    print(const.MES_PROJECT_ALREADY_EXIST.format(self.new_prj_name))
                    if response.get('Item', None):
                        raise Exception(
                            const.MES_PROJECT_ALREADY_EXIST.format(self.new_prj_name))
                    else:
                        # add new project
                        current_info['project_info'] = new_description
                        current_info['project_name'] = self.new_prj_name
                        table.put_item(
                            Item=current_info
                        )

                        # delete current prj name
                        table.delete_item(
                            Key={
                                'identity_id': identity_id,
                                'project_name': self.project_name,
                            }
                        )

                else:
                    # only update description
                    table.update_item(
                        Key={
                            'identity_id': identity_id,
                            'project_name': self.project_name,
                        },
                        ExpressionAttributeValues={
                            ':de': new_description
                        },
                        UpdateExpression='SET project_info = :de'
                    )
            else:
                raise Exception(
                    const.MES_PROJECT_NOT_FOUND.format(self.project_name))

        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        return convert_response(
            {
                'data': {
                    "project_id": current_info['project_id'],
                    "s3_prefix": current_info['s3_prefix'],
                    "is_sample": current_info['is_sample'],
                    "gen_status": current_info['gen_status'],
                    "project_name": current_info['project_name'],
                    "description": new_description
                },
                "error": False,
                "success": True,
                "message": None
            })
