import json
import boto3
import hashlib
import hmac
import base64
import os
import uuid
import requests
import random
from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, convert_current_date_to_iso8601, aws_get_identity_id
import const



def lambda_handler(event, context):
    try:
        print(event['body'])
        body = json.loads(event['body'])
        id_token = body["id_token"]
        project_id = body['project_id']
        project_name = body['project_name']
        down_type = body['down_type']

    except Exception as e:
        return convert_response({"error": True, 
                "success": False, 
                "message": "Request body format is wrong!", 
                "data": None})

    try:
        identity_id = aws_get_identity_id(id_token)
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
                
    db_resource = boto3.resource('dynamodb') 
    
        
    # create task id and save to DB
    try:
        table = db_resource.Table(os.environ["T_TASK_DOWNLOAD"])
        task_id = uuid.uuid4().hex
        create_time = convert_current_date_to_iso8601()
        table.put_item(
                Item = {
                    "identity_id": identity_id,
                    "task_id": task_id,
                    "status": "RUNNING",
                    "create_time": create_time,
                }
            )
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
                
    
    # send request to url  
    try:
        url = 'http://3.129.143.14:8000/download'
        request_body = {
            "project_id": project_id,
            "project_name": project_name,
            "down_type": down_type,
            "task_id": task_id,
            "identity_id": identity_id 
        }
        headers = { "Content-Type": "application/json" }
        response = requests.post(
            url,
            json= request_body,
            headers= headers,
        )
        
        if response.status_code == 500:
            # error when download 
            raise Exception("There are some error when downloading, please try again")
            
        value = response.json()
        print('response request: ', value)
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
    
    return convert_response(
            {
                'data': {
                        "task_id": task_id
                        },
                "error": False, 
                "success": True, 
                "message": None
            })
