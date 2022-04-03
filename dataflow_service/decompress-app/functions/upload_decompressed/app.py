import os
import json
import glob
from pathlib import Path

import boto3


EFS_MOUNT_POINT = "/mnt/efs"
BUCKET = "daita-client-data"
# prefix =

efs_mount_point = Path(EFS_MOUNT_POINT)
s3_client = boto3.client('s3')


def lambda_handler(event, context):
    print(event)

    files = event["file_chunk"]
    id_token = event["id_token"]
    project_id = event["project_id"]
    project_name = event["project_name"]
    type_method = event["type_method"]

    print(files)
    object_names = []
    for file_ in files:
        file_path = efs_mount_point.joinpath(file_)
        object_name = os.path.join("tmp", file_path.name)
        response = s3_client.upload_file(str(file_path), BUCKET, object_name)
        print(response)
        object_names.append(object_name)

    print("succeed")

    return object_names
