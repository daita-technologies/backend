import os
import json
import glob
from pathlib import Path

import boto3


PROJECT_UPLOAD_UPDATE_FUNCTION = os.getenv("PROJECT_UPLOAD_UPDATE_FUNCTION")

EFS_MOUNT_POINT = "/mnt/efs"
BUCKET = "daita-client-data"

efs_mount_point = Path(EFS_MOUNT_POINT)
s3_client = boto3.client('s3')
lambda_client = boto3.client('lambda')


def lambda_handler(event, context):
    print(event)

    files = event["file_chunk"]
    id_token = event["id_token"]
    project_id = event["project_id"]
    project_name = event["project_name"]
    type_method = event["type_method"]
    s3_prefix = event["s3_prefix"]

    print(files)
    object_names = []
    for file_ in files:
        file_path = efs_mount_point.joinpath(file_)
        object_name = os.path.join(s3_prefix, file_path.name)
        response = s3_client.upload_file(str(file_path), BUCKET, object_name)
        print(file_path, object_name, response)
        object_names.append(object_name)

    payload = {
        "id_token": id_token,
        "project_id": project_id,
        "project_name": project_name,
        "ls_object_info": ls_object_info,
        "type_method": type_method,
    }

    response = lambda_client.invoke(
        FunctionName=PROJECT_UPLOAD_UPDATE_FUNCTION,
        Payload=json.dumps(payload)
    )
    print (response)

    print("succeed")
    return object_names
