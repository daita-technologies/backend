import os
import json

import boto3
from identity_check import *
from response import *
from error_messages import *
from models.task_model import TaskModel

stepfunctions = boto3.client('stepfunctions')
task_model = TaskModel(os.environ["DecompressTaskTable"])

@error_response
def lambda_handler(event, context):
    print(event)
    queries = event["queryStringParameters"]
    id_token = queries["id_token"]
    task_id = queries["task_id"]
    
    identity_id = aws_get_identity_id(id_token)

    task_info = task_model.get_task_info_w_atribute(identity_id, task_id,
                                    ls_attribute=[TaskModel.FIELD_STATUS, TaskModel.FIELD_PROCESS_TYPE,
                                            TaskModel.FIELD_PROJECT_ID, TaskModel.FIELD_TASK_ID, 
                                            TaskModel.FIELD_UPDATED_TIME])
        
    
    if task_info is None:
        raise Exception(MESS_TASK_NOT_EXIST.format(task_id))

    print("Task return: ", task_info)

    return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=task_info,
        )    
