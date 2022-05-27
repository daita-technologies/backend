import boto3
import json
import os
import time
from config import *
from response import *
from utils import *
from identity_check import *

sqsClient = boto3.client('sqs',REGION)
sqsResourse = boto3.resource('sqs',REGION)

@error_response
def lambda_handler(event, context):
    taskQueue = sqsResourse.get_queue_by_name(QueueName=os.environ['TASK_QUEUE'])
    print(event)
    taskQueue.send_message(
                            MessageBody=json.dumps(event),
                            MessageGroupId="push-task-queue",
                            DelaySeconds=0,
                        )
    return {} 