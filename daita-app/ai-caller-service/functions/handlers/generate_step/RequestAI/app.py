from asyncio import Queue
import http
import queue
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
sqs = boto3.resource("sqs",REGION)

def deleteMessageInQueue(task):
    queueSQS = sqs.get_queue_by_name(QueueName=task['queue'])
    QueueResp = queueSQS.receive_messages(VisibilityTimeout=60,
        WaitTimeSeconds=0,MaxNumberOfMessages=1)

    print(f"Len of queueResp when deleteMessageInQueue: {len(QueueResp)}")
    for message in QueueResp :
        # messageBody = message.body
        print("Delete QUEUE with body: \n", message.body)
        # strTask = json.dumps(task)
        # # if messageBody == strTask:
        message.delete()

@error_response
def lambda_handler(event, context):
    result = event
    if result['is_retry'] == True:
        time.sleep(int(result['current_num_retries'])*2)
    print(event)

    batch = result['batch']
    print("batch :",batch)
    print("request AI body: \n", batch['request_json'])
    try :
        output = requests.post(batch['host'],json=batch['request_json'])
        print("Output from AI request: \n", output.text)
        print("Ouput AI status_code: \n", output.status_code)
        if output.status_code != http.HTTPStatus.OK:
            raise Exception("Not OK")
    except Exception as e:
        print("---------REQUEST AI exception-------\n", e)
        result['response'] = 'NOT_OK'
        result['is_retry'] = True
        if result['current_num_retries'] > result['max_retries']:
            result['is_retry'] = False
            deleteMessageInQueue(batch)
            return event
        result['current_num_retries'] += 1
        return result
    print(output.text)
    result['response'] = 'OK'
    result['is_retry'] = False
    deleteMessageInQueue(batch)
    return result