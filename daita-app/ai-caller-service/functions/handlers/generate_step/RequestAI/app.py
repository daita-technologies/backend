import http
import time
import json
import boto3
import random
import requests
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr
sqsClient = boto3.client("sqs",REGION)
## publish instance

# def uploadImageFinish()

@error_response
def lambda_handler(event, context):
    result = event
    print(event)
    batch = result['batch']
    print("request AI body: \n", batch['request_json'])
    try :
        output = requests.post(batch['host'],json=batch['request_json'])
        print("Output from AI request: \n", output.text)
        print("Ouput AI status_code: \n", output.status_code)
        if output.status_code != http.HTTPStatus.OK:
            raise Exception("Not OK")
    except Exception as e:
        result['response'] = 'NOT_OK'
        result['is_retry'] = True
        if result['current_num_retries'] > result['max_retries']:
            result['is_retry'] = False
            return event
        result['current_num_retries'] += 1
        return result
    print(output.text)
    result['response'] = 'OK'
    result['is_retry'] = False
    return result