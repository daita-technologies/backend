import os
import json

import boto3
from identity_check import *
from response import *
from error_messages import *



TASK_TABLE = os.getenv("TableDownloadTaskName")

db = boto3.resource('dynamodb')
table = db.Table(TASK_TABLE)

@error_response
def lambda_handler(event, context):
    print(event)
    queries = event["queryStringParameters"]
    id_token = queries["id_token"]
    task_id = queries["task_id"]

    identity_id = aws_get_identity_id(id_token)

    response = table.get_item(
        Key={
            "identity_id": identity_id,
            "task_id": task_id
        },
        ExpressionAttributeNames={'#ST': "status"},
        ProjectionExpression="#ST, created_at, updated_at, project_id, task_id, process_type"
    )

    task = response.get("Item", None)
    if task is None:
        raise Exception(MESS_TASK_NOT_EXIST.format(task_id))

    print("Task return: ", task)

    return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=task,
        )
