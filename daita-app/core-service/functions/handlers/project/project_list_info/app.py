from lambda_base_class import LambdaBaseClass
import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


def lambda_handler(event, context):
    return ProjectListInfoCls().handle(event, context)


class ProjectListInfoCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.id_token = body["id_token"]

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        # get identity_id from id token, also check the authentication from client
        try:
            identity_id = aws_get_identity_id(
                self.id_token, USERPOOLID, IDENTITY_POOL)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        # query list of projects
        db_resource = boto3.resource('dynamodb')
        try:
            table = db_resource.Table(os.environ['TABLE_PROJECT'])
            items_project = table.query(
                ProjectionExpression='project_name, project_id, s3_prefix, is_sample, gen_status, project_info',
                KeyConditionExpression=Key('identity_id').eq(identity_id),
            )

            table = db_resource.Table(os.environ['TABLE_TASK'])
            items_task = table.query(
                ProjectionExpression='project_id, task_id',
                KeyConditionExpression=Key('identity_id').eq(identity_id),
                FilterExpression=Attr('status').eq('RUNNING')
            )

            print(items_project)
            print(items_task)

            group_project_id = {}

            # add general project info
            for item_project in items_project['Items']:

                # update value for is_sample and gen_status
                item_project["is_sample"] = item_project.get(
                    "is_sample", False)
                item_project["gen_status"] = item_project.get(
                    "gen_status", "FINISH")
                item_project["description"] = item_project.get(
                    "project_info", "")

                group_project_id[item_project['project_id']] = item_project
                group_project_id[item_project['project_id']]['ls_task'] = []

            for item_task in items_task['Items']:
                if len(item_task.get('project_id', '')) > 0:
                    group_project_id[item_task['project_id']
                                     ]['ls_task'].append(item_task)

            table = db_resource.Table(os.environ['TABLE_PROJECT_SUMMARY'])

            for key, value in group_project_id.items():
                response = table.query(
                    KeyConditionExpression=Key('project_id').eq(key),
                )
                groups = {}
                thumnail_key = None
                for item in response['Items']:
                    type = item['type']
                    groups[type] = {
                        'count': int(item['count']),
                        'size': int(item['total_size']),
                    }
                    if item.get('thu_key', None) is not None:
                        thumnail_key = item['thu_key']

                value['groups'] = groups
                value['thum_key'] = thumnail_key

            ls_items = []
            for key, value in group_project_id.items():
                ls_items.append(value)

            print('group_project_id: ', group_project_id)

        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        return convert_response({'data': ls_items,
                                "error": False,
                                 "success": True,
                                 "message": None})
