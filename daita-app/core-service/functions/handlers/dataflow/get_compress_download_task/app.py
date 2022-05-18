import os
import json

import boto3
from identity_check import *
from response import *
from error_messages import *
from models.task_model import TaskModel


task_table = TaskModel(os.environ["TableDataFlowTaskName"], None)


@error_response
def lambda_handler(event, context):
    print(event)
    queries = event["queryStringParameters"]
    id_token = queries["id_token"]
    task_id = queries["task_id"]

    identity_id = aws_get_identity_id(id_token)

    response = task_table.table.get_item(
        Key={
            "identity_id": identity_id,
            "task_id": task_id
        },
    )

    task = response.get("Item", None)
    # pop out identity_id if needed
    task.pop("identity_id", None)
    if task is None:
        raise Exception(MESS_TASK_NOT_EXIST.format(task_id))

    print("Task return: ", task)

    return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=task,
        )
