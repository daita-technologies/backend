import os
import shutil
from datetime import datetime
from models.task_model import TaskModel

import boto3


DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")
EFS_MOUNT_POINT = os.getenv("EFSMountPath")

db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)


def convert_current_date_to_iso8601():
    now = datetime.now()
    return now.isoformat()


def lambda_handler(event, context):
    print(event)

    task_id = event["result"]["task_id"]
    identity_id = event["identity_id"]
    destination_dir = event["result"]["destination_dir"]
    # clean up extracted file dir
    efs_destination_dir = os.path.join(EFS_MOUNT_POINT, destination_dir)
    shutil.rmtree(efs_destination_dir)
    print("deteled destination folder: ", os.path.exists(efs_destination_dir))

    response = table.update_item(
        Key={"task_id": task_id,
             "identity_id": identity_id},
        ExpressionAttributeNames={'#ST': "status"},
        ExpressionAttributeValues={
            ":st": "FINISH",
            ":ua": convert_current_date_to_iso8601()
        },
        UpdateExpression=f"SET #ST = :st, {TaskModel.FIELD_UPDATED_TIME} = :ua"
    )
    print(response)

    print("succeed")

    return {
        "status": "succeed"
    }
