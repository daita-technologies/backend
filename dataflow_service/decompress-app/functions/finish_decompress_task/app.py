import os
import shutil
from datetime import datetime

import boto3


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")
EFS_MOUNT_POINT = "/mnt/efs"

db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)


def convert_current_date_to_iso8601():
    now = datetime.now()
    return now.isoformat()


def lambda_handler(event, context):
    print(event)

    task_id = event["task_id"]
    destination_dir = event["destination_dir"]
    # clean up extracted file dir
    efs_destination_dir = os.path.join(EFS_MOUNT_POINT, destination_dir)
    shutil.rmtree(efs_destination_dir)
    print("efs_destination_dir exists: ", os.path.exists(efs_destination_dir))

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
