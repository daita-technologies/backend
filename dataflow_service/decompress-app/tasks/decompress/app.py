import os
import subprocess
from datetime import datetime

import boto3


EFS_MOUNT_POINT = "/mnt/efs"
APP_PREFIX = "app/decompress"
DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")

TASK_ID = os.getenv("TASK_ID")
FILE_URL = os.getenv("FILE_URL")

db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)


def convert_current_date_to_iso8601():
    now = datetime.now()
    return now.isoformat()


def update_task_status(status):
    table.update_item(
        Key={"id": TASK_ID},
        ExpressionAttributeNames={'#ST': "status"},
        ExpressionAttributeValues={
            ":st": status,
            ":ua": convert_current_date_to_iso8601()
        },
        UpdateExpression="SET #ST = :st, updated_at = :ua"
    )


def main():
    # working_dir = os.path.join(APP_PREFIX, TASK_ID)
    work_dir = os.path.join(APP_PREFIX, "tmp")
    filename = os.path.basename(FILE_URL)
    file_stemp = os.path.splitext(filename)[0]
    destination_dir = os.path.join(work_dir, file_stemp)

    table.update_item(
        Key={"id": TASK_ID},
        ExpressionAttributeNames={'#ST': "status"},
        ExpressionAttributeValues={
            ":st": "RUNNING",
            ":ua": convert_current_date_to_iso8601(),
            ":dst": destination_dir
        },
        UpdateExpression="SET #ST = :st, updated_at = :ua, destination_dir = :dst"
    )

    efs_work_dir = os.path.join(EFS_MOUNT_POINT, work_dir)
    efs_destination_dir = os.path.join(EFS_MOUNT_POINT, destination_dir)

    commands = [
        f"mkdir -p {efs_work_dir}",
        f"cd {efs_work_dir}",
        f"/usr/local/bin/aws s3 cp {FILE_URL} {filename}",
        f"unzip {filename} -d {efs_destination_dir}",
        f"rm {filename}"
    ]
    command = " && ".join(commands)

    try:
        subprocess.run(command, capture_output=True, shell=True)
    except Exception:
        update_task_status("ERROR")


if __name__ == "__main__":
    main()
