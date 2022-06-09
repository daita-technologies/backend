import os
import time
import json
import boto3
import random
import shutil
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr
from models.task_model import TaskModel
from models.generate_task_model import GenerateTaskModel

generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])
task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"],None)

@error_response
def lambda_handler(event, context):
    time.sleep(event['current_retry']*10)
    item = generate_task_model.get_task_info(event['identity_id'],event['task_id'])
    if event['status'] == 'ERROR':
        event['is_retry'] = False
        return event
    if event['message_in_flight'] == item.number_finished:
        task_model.update_status(event['task_id'], event['identity_id'], event['status'])
        if event['status'] == 'FINISH':
            folder = os.environ['ROOTEFS'] + os.environ['EFSPATH'] +'/'+ event['task_id'] +'/'
            if os.path.exists(folder):
                shutil.rmtree(folder)
        event['is_retry'] = False
        return event
    if event['current_retry'] <= event['retry_waiting_message_in_flight']:
        event['current_retry'] += 1
    else:
        event['is_retry'] = False
        task_id = event['task_id']
        print(f'The curreny message in flight { item.messages_in_flight} , task id:  {task_id} ')
        task_model.update_status(event['task_id'], event['identity_id'], 'ERROR')
    return event