import os
from datetime import datetime

import boto3


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")
EFS_FILE_SYSTEM_ID = os.getenv("FileSystemId")

db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)
efs_client = boto3.client('efs')


def convert_current_date_to_iso8601():
    now = datetime.now()
    return now.isoformat()


def lambda_handler(event, context):
    print(event)

    task_id = event["task_id"]
    destination_dir = event["destination_dir"]

    # clean up extracted file dir
    response = efs_client.delete_tags(
        FileSystemId=EFS_FILE_SYSTEM_ID,
        TagKeys=[destination_dir]
    )
    print(response)

    response = table.update_item(
        Key={"id": task_id},
        ExpressionAttributeNames={'#ST': "status"},
        ExpressionAttributeValues={
            ":st": "FINISHED",
            ":ua": convert_current_date_to_iso8601()
        },
        UpdateExpression="SET #ST = :st, updated_at = :ua"
    )
    print(response)

    print("succeed")

    return {
        "status": "succeed"
    }
