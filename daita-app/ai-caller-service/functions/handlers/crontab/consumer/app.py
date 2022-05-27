import boto3
import json
import os
import time
from boto3.dynamodb.conditions import Key, Attr
from models.generate_task_model import GenerateTaskModel
from config import *
from response import *
from utils import *
from identity_check import *

generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])
sqsClient = boto3.client('sqs',REGION)
sqsResourse = boto3.resource('sqs',REGION)
client_events = boto3.client('events')  

@error_response
def lambda_handler(event, context):
    timeout_start = time.time()
    while True:
        if time.time() - timeout_start >= 45:
            break
        queueSQS = sqsResourse.get_queue_by_name(QueueName=os.environ['TASK_QUEUE'])
        QueueResp = queueSQS.receive_messages(VisibilityTimeout=10,
            WaitTimeSeconds=0,MaxNumberOfMessages=10)
        pushedMessage = 0 
        maxPushedMessage = int(os.environ.get('MAX_CONCURRENCY_TASKS','2'))
        for index ,message in enumerate(QueueResp) :
            body = json.loads(message.body)
            detail = body["detail"]
            item = generate_task_model.get_task_info(detail['identity_id'] ,detail['task_id'])
            print(item.status,item.waitingInQueue)
            if item.status == 'FINISH' or item.status == 'CANCEL' or item.status == 'FINISH_ERROR':
                message.delete()
            if item.status != 'PENDING' or not item.waitingInQueue:
                pushedMessage += 1
            elif item.status == 'PENDING' and pushedMessage < maxPushedMessage and item.waitingInQueue:
                response = client_events.put_events(
                                    Entries=[
                                        {
                                            'Source': 'source.events',
                                            'DetailType': 'lambda.event',
                                            'Detail': json.dumps(detail),
                                            'EventBusName': os.environ["EVENT_BUS_NAME"]
                                        },
                                    ]
                                )
                generate_task_model.update_task_dequeue(detail['identity_id'] ,detail['task_id'])
                pushedMessage += 1
                print(response)
        time.sleep(5)
    return {}