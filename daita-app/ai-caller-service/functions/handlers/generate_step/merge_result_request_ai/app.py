import time
import json
import os
import boto3
import random
import shutil
import glob
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr


@error_response
def lambda_handler(event, context):
    result = {"state": "", "response": "OK"}
    batches = event
    lenBatches = len(batches)
    task_finish = 0
    for batch in batches:
        if batch["response"] == "OK":
            task_finish += 1
    if task_finish == 0:
        result["response"] = "NOT_OK"
        result["state"] = "ERROR"
        result["status"] = "ERROR"
    elif task_finish == lenBatches:
        result["status"] = "FINISH"
        result["state"] = "FINISH"
    else:
        result["status"] = "FINISH_ERROR"
        result["state"] = "FINISH"
    result["retry_waiting_message_in_flight"] = 10
    result["current_retry"] = 1
    result["is_retry"] = True
    return result
