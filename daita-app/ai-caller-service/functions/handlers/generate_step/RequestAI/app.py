import os
import http
import queue
import time
import json
import glob
import boto3
import random
import requests
from datetime import datetime
from config import *
from response import *
from utils import *
from s3_utils import split
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr
from models.generate_task_model import GenerateTaskModel
s3 = boto3.client('s3')
sqs = boto3.resource("sqs", REGION)
sqsClient = boto3.client('sqs', REGION)
ec2_resource = boto3.resource('ec2', region_name=REGION)
Mode = os.environ.get(
    'MODE', 'staging'
)
generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])


def deleteMessageInQueue(task):
    queueSQS = sqs.get_queue_by_name(QueueName=task['queue'])
    QueueResp = queueSQS.receive_messages(VisibilityTimeout=60,
                                          WaitTimeSeconds=0, MaxNumberOfMessages=1)

    print(f"Len of queueResp when deleteMessageInQueue: {len(QueueResp)}")
    for message in QueueResp:
        # messageBody = message.body
        mss_id = message.message_id
        print("Delete QUEUE with id: \n", mss_id)
        # delete_message= sqsClient.delete_message(QueueUrl=QueueUrl, ReceiptHandle=msg["ReceiptHandle"])

        # # strTask = json.dumps(task)
        # # # if messageBody == strTask:
        message.delete()

    print(
        f"--Count AFTER DELETE message in queue: {task['queue']} is {countTaskInQueue(task['queue'])}")


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
        time.sleep(int(result['current_num_retries'])*15)
    print("Input event: ", event)
    batch = result['batch']
    if not isinstance(batch['request_json']['images_paths'], list):
        bucket, filename = split(batch['request_json']['images_paths'])
        resultS3 = s3.get_object(Bucket=bucket, Key=filename)
        batch['request_json']['images_paths'] = json.loads(
            resultS3["Body"].read().decode())
    ######################## Hot Fix for dev enviroment#########
    if Mode == 'dev' and len(batch['request_json']['images_paths']) != 0:
        tmpStr = batch['request_json']['images_paths'][0]
        tmp = tmpStr.split('/')[0]
        if tmp != 'generation-task':
            tmpArr = tmpStr.split('/')
            index = None
            for it, el in enumerate(tmpArr):
                if el == 'generation-task':
                    index = it
            tmpbatch = batch['request_json']['images_paths']
            tmpStr = None
            batchArr = []
            for it in tmpbatch:
                tmpStr = it.split('/')
                batchArr.append('/'.join(tmpStr[index:]))
            batch['request_json']['images_paths'] = batchArr
            outputTmp = (batch['request_json']['output_folder']).split('/')
            batch['request_json']['output_folder'] = '/'.join(
                outputTmp[index:])
    ######################################################
    item = generate_task_model.get_task_info(
        result['identity_id'], result['task_id'])
    if item.status == 'CANCEL':
        result['response'] = 'NOT_OK'
        result['is_retry'] = False
        deleteMessageInQueue(batch)
        return result

    print(
        f"--Count current message in queue: {batch['queue']} is {countTaskInQueue(batch['queue'])}")

    print("request AI body: \n", batch['request_json'])
    result['output_images'] = []
    try:
        instance = ec2_resource.Instance(batch['ec2_id'])
        instance.load()
        print(
            f"Current state of instance before send request: {batch['ec2_id']} is {instance.state['Name']}")
        ip_public_current = instance.public_ip_address
        print(f"Current IP public {ip_public_current} and {batch['host']}")
        if not str(ip_public_current) in batch['host']:
            batch['host'] = f"http://{ip_public_current}:8000/{batch['type']}"
            print(batch['host'])
        output = requests.post(batch['host'], json=batch['request_json'])

        # use augment_codes for gen_id method for all images in batch
        json_data = output.json()
        result["augment_codes"] = json_data.get("augment_codes", None)
        print("Output from AI request: \n", output.text)

        if output.status_code != http.HTTPStatus.OK:
            raise Exception("Not OK")
        result['output_images'] = json_data['images_paths']
    except Exception as e:
        print("---------REQUEST AI exception-------\n", e)
        result['response'] = 'NOT_OK'
        result['is_retry'] = True
        result["augment_codes"] = None
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
