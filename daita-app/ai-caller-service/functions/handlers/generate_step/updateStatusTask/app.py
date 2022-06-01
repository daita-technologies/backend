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
    task_model.update_status(event['task_id'], event['identity_id'], event['status'])
    print(event)
    if event['status'] == 'FINISH':
        folder = os.environ['ROOTEFS'] + os.environ['EFSPATH'] +'/'+ event['task_id'] +'/'
        if os.path.exists(folder):
            shutil.rmtree(folder)
    return generate_response(
        message="OK",
        status_code=HTTPStatus.OK
    )