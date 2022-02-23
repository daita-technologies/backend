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
        table = dynamodb.Table(os.environ['T_METHODS'])
        response = table.scan()              
        items = response['Items']
        dict_type = {
            "augmentation": [],
            "preprocessing": []
        }
        for item in items:
            if 'AUG' in item['method_id']:
                dict_type['augmentation'].append(item)
            elif 'PRE' in item['method_id']:
                dict_type['preprocessing'].append(item)
            else:
                dict_type['preprocessing'].append(item)
                
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None}) 
   
    return convert_response({'data': dict_type, 
            "error": False, 
            "success": True, 
            "message": None})
    