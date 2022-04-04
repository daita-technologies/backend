import os
from datetime import datetime

import boto3


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")

db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)


def convert_current_date_to_iso8601():
    now = datetime.now()
    return now.isoformat()


def lambda_handler(event, context):
    print(event)

    task_id = event["task_id"]

    response = table.update_item(
        Key={"id": task_id},
        ExpressionAttributeNames={'#ST': "status"},
        ExpressionAttributeValues={
            ":st": "FINISHED",
            ":ua": convert_current_date_to_iso8601()
        },
        UpdateExpression="SET #ST = :st, updated_at = :ua"
    )

    print("succeed")
