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

task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"])

@error_response
def lambda_handler(event, context):

    task_model.update_status(event['task_id'], event['identity_id'], event['status'])

    return generate_response(
        message="OK",
        status_code=HTTPStatus.OK
    )