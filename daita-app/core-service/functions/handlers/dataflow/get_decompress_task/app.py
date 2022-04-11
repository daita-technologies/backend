import os
import json

import boto3


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")

stepfunctions = boto3.client('stepfunctions')
db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)

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
        ProjectionExpression="task_id, #ST, created_at, updated_at"
    )
    print(response)
    task = response["Item"]
    print(task)
    task["task_id"] = task.pop("task_id")

    print("succeed")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "succeed",
            **task
        }),
    }
