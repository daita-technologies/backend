import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr

from utils import convert_response, aws_get_identity_id

MAX_NUMBER_LIMIT = 500


def lambda_handler(event, context):

    # try to parse request body and check body fields
    try:
        print(event['body'])
        body = json.loads(event['body'])
        id_token = body["id_token"]
        project_id = body["project_id"]
        type_method = body["type_method"]
        next_token = body["next_token"]
        num_limit = min(MAX_NUMBER_LIMIT, body.get(
            "num_limit", MAX_NUMBER_LIMIT))

    except Exception as e:
        return convert_response({"error": True,
                                 "success": False,
                                 "message": repr(e),
                                 "data": None})

    # get identity_id from id token, also check the authentication from client
    try:
        identity_id = aws_get_identity_id(id_token)
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True,
                                 "success": False,
                                 "message": repr(e),
                                 "data": None})

    # query list data of project
    dynamodb = boto3.resource('dynamodb')
    try:
        if type_method == 'ORIGINAL':
            table_name = os.environ['T_DATA_ORI']
        elif type_method == 'PREPROCESS':
            table_name = os.environ['T_DATA_PREPROCESS']
        elif type_method == 'AUGMENT':
            table_name = os.environ['T_DATA_AUGMENT']
        else:
            raise (Exception(f'type_method: {type_method} is not valid!'))

        table = dynamodb.Table(table_name)
        if len(next_token) == 0:
            response = table.query(
                IndexName='index-created-sorted',
                KeyConditionExpression=Key('project_id').eq(project_id),
                ProjectionExpression='filename, s3_key, type_method, gen_id, created_date',
                Limit=num_limit,
                ScanIndexForward=False
            )
            print('___Response first: ___', response)
        else:
            response = table.query(
                IndexName='index-created-sorted',
                KeyConditionExpression=Key('project_id').eq(project_id),
                ProjectionExpression='filename, s3_key, type_method, gen_id, created_date',
                ExclusiveStartKey=next_token,
                Limit=num_limit,
                ScanIndexForward=False
            )
            print('___Response next: ___', response)

        next_token = None
        # LastEvaluatedKey indicates that there are more results
        if 'LastEvaluatedKey' in response:
            next_token = response['LastEvaluatedKey']

    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True,
                                 "success": False,
                                 "message": repr(e),
                                 "data": None})

    return convert_response({'data': {
        'items': response['Items'],
        'next_token': next_token
    },
        "error": False,
        "success": True,
        "message": None})
