import os
import json
import uuid
from datetime import datetime

import boto3


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")

stepfunctions = boto3.client('stepfunctions')
db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)


def convert_current_date_to_iso8601():
    now = datetime.now()
    return now.isoformat()


def lambda_handler(event, context):
    print(event)
    body = json.loads(event["body"])

    # file path in S3
    file_url = body["file_url"]
    id_token = body["id_token"]
    project_id = body['project_id']
    project_name = body['project_name']
    type_method = body.get('type_method', 'ORIGINAL')

    # task_id = str(uuid.uuid4())
    task_id = "d34986e9-ceb3-45c0-ac3b-cc84d9e44259"
    response = table.put_item(
        Item={
            "id": task_id,
            "status": "CREATED",
            "created_at": convert_current_date_to_iso8601(),
            "updated_at": convert_current_date_to_iso8601(),
        }
    )

    task_input = {
        "file_url": file_url,
        "task_id": task_id,
        "id_token": id_token,
        "project_id": project_id,
        "project_name": project_name,
        "type_method": type_method,
    }
    response = stepfunctions.start_execution(
        stateMachineArn=os.getenv("DecompressFileStateMachineArn"),
        input=json.dumps(task_input)
    )

    print("succeed")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "succeed",
            "task_id": task_id,
            "file_url": file_url
        }),
    }
