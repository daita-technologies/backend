import os
import json
import uuid
from datetime import datetime

import boto3
from response import *
from error_messages import *
from identity_check import *
from utils import create_unique_id, convert_current_date_to_iso8601



DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")
PROJECTS_TABLE = os.getenv("ProjectsTable")

stepfunctions = boto3.client('stepfunctions')
db = boto3.resource('dynamodb')
task_table = db.Table(DECOMPRESS_TASK_TABLE)
projects_table = db.Table(PROJECTS_TABLE)

@error_response
def lambda_handler(event, context):
    print(event)
    body = json.loads(event["body"])

    # file path in S3
    file_url = body["file_url"]
    id_token = body["id_token"]
    project_id = body['project_id']
    project_name = body['project_name']
    type_method = body.get('type_method', 'ORIGINAL')
    
    identity_id = aws_get_identity_id(id_token)

    task_id = create_unique_id()
    response = task_table.put_item(
        Item={
            "identity_id": identity_id,
            "task_id": task_id,
            "file_url": file_url,
            "status": "CREATED",
            "created_at": convert_current_date_to_iso8601(),
            "updated_at": convert_current_date_to_iso8601(),
        }
    )
        
    response = projects_table.get_item(
        Key={
            "identity_id": identity_id,
            "project_name": project_name
        },
        ProjectionExpression="s3_prefix"
    )
    print(response)
    s3_prefix = response["Item"].get("s3_prefix")

    stepfunction_input = {
        "file_url": file_url,
        "task_id": task_id,
        "id_token": id_token,
        "project_id": project_id,
        "project_name": project_name,
        "type_method": type_method,
        "s3_prefix": s3_prefix,
        "identity_id": identity_id
    }
    response = stepfunctions.start_execution(
        stateMachineArn=os.getenv("DecompressFileStateMachineArn"),
        input=json.dumps(stepfunction_input)
    )

    return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data= {
                "task_id": task_id,
                "file_url": file_url,
            }
        )
