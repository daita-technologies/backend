import os
import glob
import subprocess
from datetime import datetime

import boto3


EFS_MOUNT_POINT = os.getenv("EFSMountPath")
DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")

TASK_ID = os.getenv("TASK_ID")
FILE_URL = os.getenv("FILE_URL")
INDENTITY_ID = os.getenv("INDENTITY_ID")

db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)

def convert_current_date_to_iso8601():
    now = datetime.now()
    return now.isoformat()

def update_task_status(status):
    table.update_item(
        Key={
            "identity_id": INDENTITY_ID,
            "task_id": TASK_ID
        },
        ExpressionAttributeNames={'#ST': "status"},
        ExpressionAttributeValues={
            ":st": status,
            ":ua": convert_current_date_to_iso8601()
        },
        UpdateExpression="SET #ST = :st, updated_time = :ua"
    )

def main():
    work_dir = TASK_ID
    filename = os.path.basename(FILE_URL)
    file_stemp = os.path.splitext(filename)[0]
    destination_dir = os.path.join(work_dir, file_stemp)

    try:
        table.update_item(
            Key={
                "identity_id": INDENTITY_ID,
                "task_id": TASK_ID
            },
            ExpressionAttributeNames={'#ST': "status"},
            ExpressionAttributeValues={
                ":st": "RUNNING",
                ":ua": convert_current_date_to_iso8601(),
                ":dst": destination_dir
            },
            UpdateExpression="SET #ST = :st, updated_time = :ua, destination_dir = :dst"
        )

        efs_work_dir = os.path.join(EFS_MOUNT_POINT, work_dir)
        efs_destination_dir = os.path.join(EFS_MOUNT_POINT, destination_dir)

        commands = [
            f"mkdir -p '{efs_work_dir}'",
            f"cd '{efs_work_dir}'",
            f"/usr/local/bin/aws s3 cp '{FILE_URL}' '{filename}'",
            f"unzip -j -d '{efs_destination_dir}' '{filename}'",
            f"rm '{filename}'"
        ]
        command = " && ".join(commands)

        subprocess.run(command, shell=True)
    except Exception:
        update_task_status("ERROR")

    nrof_files = glob.glob(os.path.join(efs_destination_dir, "*"))
    print(f"Extracted {nrof_files} files from {filename}")

if __name__ == "__main__":
    main()
