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
from task import TasksModel
taskModel = TasksModel()

@error_response
def lambda_handler(event, context):
    taskModel.update_final(task_id= event['task_id'],identity_id=event['identity_id'],status=event['status'])
    return generate_response(
         message="OK",
        status_code=HTTPStatus.OK
    )