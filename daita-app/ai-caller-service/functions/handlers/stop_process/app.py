import boto3
import json
import os
import time
from config import *
from response import *
from utils import *
from identity_check import *
from models.generate_task_model import GenerateTaskModel
import concurrent.futures

generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])
CONCURRENCY = 3
sfn_client = boto3.client("stepfunctions")


def stop_parent_execution(execARN):
    return sfn_client.stop_execution(executionArn=execARN)


def stop_children_execution(execArn):
    a = sfn_client.get_execution_history(executionArn=execArn, reverseOrder=True)
    for it in a["events"]:
        if it["type"] == "TaskSubmitted":
            output = json.loads(it["taskSubmittedEventDetails"]["output"])
            print(output["ExecutionArn"])
            stop_parent_execution(output["ExecutionArn"])


def process(identity_id, task_id):
    item = generate_task_model.get_task_info(identity_id, task_id)
    executeArn = item.executeArn
    stop_parent_execution(execARN=executeArn)
    stop_children_execution(execArn=executeArn)
    generate_task_model.update_status(identity_id, task_id, "CANCEL")


@error_response
def lambda_handler(event, context):
    body = event["detail"]
    process(identity_id=body["identity_id"], task_id=body["task_id"])
    print("STOP")
    return {}
