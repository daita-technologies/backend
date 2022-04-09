import os
import json

import boto3


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")

stepfunctions = boto3.client('stepfunctions')
db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)


def lambda_handler(event, context):
    print(event)
    queries = event["queryStringParameters"]
    task_id = queries["task_id"]

    response = table.get_item(
        Key={"id": task_id},
        ExpressionAttributeNames={'#ST': "status"},
        ProjectionExpression="id, #ST, created_at, updated_at"
    )
    print(response)
    task = response["Item"]
    task["task_id"] = task.pop("id")

    print("succeed")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "succeed",
            **task
        }),
    }
