import boto3
import json
import os
import time
from config import *
from response import *
from utils import *
from identity_check import *
from models.generate_task_model import GenerateTaskModel
sfn_client = boto3.client('stepfunctions')
generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])

def stop_execution(execARN):
    return sfn_client.stop_execution(
    executionArn=execARN)

def check_state_machine(execArn):
    a =sfn_client.get_execution_history(executionArn=execArn)
    isCheckGenerateTask =  False
    for it in a['events']:
        if it['type'] == 'TaskStateEntered' and it['stateEnteredEventDetails']['name'] == 'GenerateTask':
            isCheckGenerateTask = True
            break
    return isCheckGenerateTask


def process( identity_id, task_id):
    item = generate_task_model.get_task_info(identity_id,task_id)
    executeArn = item.executeArn

    isCheckGenerateTask = check_state_machine(execArn=executeArn)
    if not isCheckGenerateTask:
        stop_execution(executeArn)
    elif item.status != 'RUNNING':
            stop_execution(executeArn)
    # stop_execution(executeArn)
    # if not item.status in ['FINISH','ERROR','FINISH_ERROR']: 
    generate_task_model.update_status(identity_id,task_id,'CANCEL')
@error_response
def lambda_handler(event, context):
    body = event['detail']
    process(identity_id=body['identity_id'],task_id=body['task_id'])
    print("STOP")
    return {}