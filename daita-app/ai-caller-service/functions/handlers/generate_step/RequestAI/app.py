import os
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
from models.generate_task_model import GenerateTaskModel

sqs = boto3.resource("sqs",REGION)
sqsClient = boto3.client('sqs',REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)

generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])

def deleteMessageInQueue(task):
    queueSQS = sqs.get_queue_by_name(QueueName=task['queue'])
    QueueResp = queueSQS.receive_messages(VisibilityTimeout=60,
        WaitTimeSeconds=0,MaxNumberOfMessages=1)

    print(f"Len of queueResp when deleteMessageInQueue: {len(QueueResp)}")
    for message in QueueResp :
        # messageBody = message.body
        mss_id = message.message_id
        print("Delete QUEUE with id: \n", mss_id)
        # delete_message= sqsClient.delete_message(QueueUrl=QueueUrl, ReceiptHandle=msg["ReceiptHandle"])

        # # strTask = json.dumps(task)
        # # # if messageBody == strTask:
        message.delete()

    print(f"--Count AFTER DELETE message in queue: {task['queue']} is {countTaskInQueue(task['queue'])}")

def getQueue(queue_name_env):
    response = sqsClient.get_queue_url(QueueName=queue_name_env)
    return response['QueueUrl']

def countTaskInQueue(queue_id):
    # get_queue_attributes
    # sqsName = sqsResourse.get_queue_by_name(QueueName=queue_id)
    response = sqsClient.get_queue_attributes(
                            QueueUrl=getQueue(queue_id),
                            AttributeNames=[
                                'ApproximateNumberOfMessages'
                            ]
                        )
    num_task_in_queue = response['Attributes']['ApproximateNumberOfMessages']
    return int(num_task_in_queue)

@error_response
def lambda_handler(event, context):
    result = event
    if result['is_retry'] == True:
        time.sleep(int(result['current_num_retries'])*30)

    print("Input event: ", event)

    batch = result['batch']
    item = generate_task_model.get_task_info(result['identity_id'] ,result['task_id'])
    if item.status == 'CANCEL':
        result['response'] = 'NOT_OK'
        result['is_retry'] = False
        deleteMessageInQueue(batch)
        return result
    
    print(f"--Count current message in queue: {batch['queue']} is {countTaskInQueue(batch['queue'])}")  
    print("request AI body: \n", batch['request_json'])
    try :
        instance = ec2_resource.Instance(batch['ec2_id'])
        instance.load()
        print(f"Current state of instance before send request: {batch['ec2_id']} is {instance.state['Name']}")

        output = requests.post(batch['host'],json=batch['request_json'])
        print("Output from AI request: \n", output.text)

        if output.status_code != http.HTTPStatus.OK:
            raise Exception("Not OK")
    except Exception as e:
        print("---------REQUEST AI exception-------\n", e)
        result['response'] = 'NOT_OK'
        result['is_retry'] = True
        if result['current_num_retries'] > result['max_retries']:
            result['is_retry'] = False
            print("-----Delete message with exception from AI request")
            deleteMessageInQueue(batch)
            return event
        result['current_num_retries'] += 1
        return result
    # print(output.text)
    result['response'] = 'OK'
    result['is_retry'] = False
    print("-----Normal Delete message ------------------------ ")
    deleteMessageInQueue(batch)

    return result