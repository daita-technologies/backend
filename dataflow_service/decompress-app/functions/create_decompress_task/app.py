import os
import json
import uuid
from datetime import datetime

import boto3


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")
PROJECTS_TABLE = os.getenv("ProjectsTable")

stepfunctions = boto3.client('stepfunctions')
db = boto3.resource('dynamodb')
task_table = db.Table(DECOMPRESS_TASK_TABLE)
projects_table = db.Table(PROJECTS_TABLE)


# Calling Cognito from VPC is hard so I move it here
# ref: https://stackoverflow.com/a/62360784
def aws_get_identity_id(id_token):
    identity_client = boto3.client('cognito-identity')
    PROVIDER = f'cognito-idp.{identity_client.meta.region_name}.amazonaws.com/{os.getenv("USER_POOL_ID")}'
    try:
        identity_response = identity_client.get_id(
                              IdentityPoolId=os.getenv('IDENTITY_POOL_ID'),
                              Logins = {PROVIDER: id_token})
    except Exception as e:
        print('Error: ', repr(e))
        raise
    identity_id = identity_response['IdentityId']
    return identity_id


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

    task_id = str(uuid.uuid4())
    # task_id = "d31f5fe2-7bcb-47f7-9e97-eb6d08d32afd" #mock
    response = task_table.put_item(
        Item={
            "id": task_id,
            "file_url": file_url,
            "status": "CREATED",
            "created_at": convert_current_date_to_iso8601(),
            "updated_at": convert_current_date_to_iso8601(),
            # "destination_dir": f"app/decompress/{task_id}/test" #mock
        }
    )

    identity_id = aws_get_identity_id(id_token)
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
    }
    response = stepfunctions.start_execution(
        stateMachineArn=os.getenv("DecompressFileStateMachineArn"),
        input=json.dumps(stepfunction_input)
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
