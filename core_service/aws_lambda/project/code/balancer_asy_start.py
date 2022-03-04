import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr

from utils import convert_response, aws_get_identity_id, dydb_get_task_progress

MAX_NUMBER_LIMIT = 500

def lambda_handler(event, context):

    # try to parse request body and check body fields
    try:
        print(event['body'])
        body = json.loads(event['body'])
        id_token = body["id_token"]
        task_id = body["task_id"]        

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

    # get infor of task_id
    dynamodb = boto3.resource('dynamodb')
    try:
        table = dynamodb.Table(os.environ['T_TASKS'])
        items = dydb_get_task_progress(table, identity_id, task_id)               
        if items is not None:
            items['number_finished'] = int(items['number_finished'])
            items['number_gen_images'] = int(items['number_gen_images'])
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None}) 
   
    return convert_response({'data': items, 
            "error": False, 
            "success": True, 
            "message": None})
    