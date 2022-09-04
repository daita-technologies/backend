from http.client import responses
from lambda_base_class import LambdaBaseClass
import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr

from utils import convert_response, aws_get_identity_id

MAX_NUMBER_LIMIT = 500
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


def lambda_handler(event, context):
    return ProjectListCls().handle(event, context)


class ProjectListCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_id = body["project_id"]
        self.type_method = body["type_method"]
        self.next_token = body["next_token"]
        self.num_limit = min(MAX_NUMBER_LIMIT, body.get(
            "num_limit", MAX_NUMBER_LIMIT))

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

        # query list data of project
        dynamodb = boto3.resource('dynamodb')
        try:
            if self.type_method == 'ORIGINAL':
                table_name = os.environ['T_DATA_ORI']
            elif self.type_method == 'PREPROCESS':
                table_name = os.environ['T_DATA_PREPROCESS']
            elif self.type_method == 'AUGMENT':
                table_name = os.environ['T_DATA_AUGMENT']
            else:
                raise (
                    Exception(f'type_method: {self.type_method} is not valid!'))

            table = dynamodb.Table(table_name)
            if len(self.next_token) == 0:
                response = table.query(
                    IndexName='index-created-sorted',
                    KeyConditionExpression=Key(
                        'project_id').eq(self.project_id),
                    # ProjectionExpression='filename, s3_key, type_method, gen_id, created_date',
                    Limit=self.num_limit,
                    ScanIndexForward=False
                )
                print('___Response first: ___', response)
            else:
                response = table.query(
                    IndexName='index-created-sorted',
                    KeyConditionExpression=Key(
                        'project_id').eq(self.project_id),
                    # ProjectionExpression='filename, s3_key, type_method, gen_id, created_date',
                    ExclusiveStartKey=self.next_token,
                    Limit=self.num_limit,
                    ScanIndexForward=False
                )
                print('___Response next: ___', response)

            self.next_token = None
            # LastEvaluatedKey indicates that there are more results
            if 'LastEvaluatedKey' in response:
                self.next_token = response['LastEvaluatedKey']

        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})
        items =[]
        for it in response['Items']:
            tempItem = {
                'created_date':it['created_date'],
                'filename': it['filename'],
                'gen_id':it['gen_id'],
                'type_method':it['type_method']
            }
            if 'thumbnail' in it and  bool(it['thumbnail']):
                tempItem['s3_key'] = it['thumbnail'].replace('s3://','')
            else:
                tempItem['s3_key'] = it['s3_key']
            items.append(tempItem)
        return convert_response({'data': {
            'items': items,
            'next_token': self.next_token
        },
            "error": False,
            "success": True,
            "message": None})
