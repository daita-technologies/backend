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
                
    try:
        db_resource = boto3.resource('dynamodb')
        table = db_resource.Table(os.environ['T_INSTANCES'])
        
        # check identity_id exist instance or not
        response = table.query(
                KeyConditions = {
                        'assi_id': identity_id
                    }
            )
        if response.get('Items'):
            if len(response['Items'])>0:
                raise Exception(f"This id {identity_id} already assiged to an instance before!")
        
        # check list ec2_id available
        response = table.query(
                KeyConditions = {
                        'assi_id': "free"
                    }
            )
        
        if response.get('Items') and len(response['Items'])>0:
            # update assign one to id in DB
            pass
        else:
            # no ec2 free for assigning, assign to general id
            pass
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
   
    return convert_response({'data': None, 
            "error": False, 
            "success": True, 
            "message": None})
    