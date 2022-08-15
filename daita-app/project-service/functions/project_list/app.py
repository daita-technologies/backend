import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id


def lambda_handler(event, context):

    # try to parse request body and check body fields
    try:
        print(event['body'])
        body = json.loads(event['body'])
        id_token = body["id_token"]
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

    # query list of projects
    db_resource = boto3.resource('dynamodb')
    try:
        table = db_resource.Table(os.environ['T_PROJECT'])
        items = table.query(
            ProjectionExpression='project_name, project_id, s3_prefix, is_sample, gen_status',
            KeyConditionExpression=Key('identity_id').eq(identity_id),
        )
        ls_item = []
        if items.get("Items", None):
            for item in items["Items"]:
                item["is_sample"] = item.get("is_sample", False)
                item["gen_status"] = item.get("gen_status", "FINISH")
                ls_item.append(item)

    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True,
                                 "success": False,
                                 "message": repr(e),
                                 "data": None})

    return convert_response({'data': {
        'items': ls_item
    },
        "error": False,
        "success": True,
        "message": None})
