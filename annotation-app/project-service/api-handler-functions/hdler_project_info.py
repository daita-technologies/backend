

from lambda_base_class import LambdaBaseClass
import json
import boto3
import os

from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id, dydb_get_project_full

USERPOOLID = os.environ['COGNITO_USER_POOL']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


class ProjectInfoCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_name = body["project_name"]

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        try:
            identity_id = aws_get_identity_id(
                
                self.id_token, USERPOOLID, IDENTITY_POOL)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        db_resource = boto3.resource('dynamodb')
        # get project_id
        try:
            table = db_resource.Table(os.environ['TABLE_ANNO_PROJECT'])
            res_project = dydb_get_project_full(
                table, identity_id, self.project_name)

            # print(res_projectid)
            res_projectid = res_project['project_id']
            is_sample = res_project.get("is_sample", False)

        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                      "message": repr(e),
                                      "data": None})

        # get info detail of a project
        try:
            table = db_resource.Table(os.environ['TABLE_ANNO_PROJECT_SUMMARY'])
            response = table.query(
                KeyConditionExpression=Key('project_id').eq(res_projectid),
            )
            # print(response)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                      "message": repr(e),
                                      "data": None})

        if response.get('Items', None):
            groups = {}
            for item in response['Items']:
                type = item['type']
                data_num = res_project.get(type, None)
                if data_num is not None:
                    data_num = [int(a) for a in data_num]
                groups[type] = {
                    'count': int(item['count']),
                    'size': int(item['total_size']),
                    'data_number': data_num
                }

            return convert_response({'data': {
                "identity_id": identity_id,
                "project_name": self.project_name,
                "project_id": res_projectid,
                "is_sample": is_sample,
                "groups": groups,
            },
                "error": False,
                "success": True,
                "message": None})
        else:
            return convert_response({'data': {
                "identity_id": identity_id,
                "project_name": self.project_name,
                "project_id": res_projectid,
                "is_sample": is_sample,
                "ls_task": [],
                "groups": None,
            },
                "error": False,
                "success": True,
                "message": None})


def lambda_handler(event, context):
    return ProjectInfoCls().handle(event=event,  context=context)