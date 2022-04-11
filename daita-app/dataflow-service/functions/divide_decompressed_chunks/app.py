import os
import json
import glob

import boto3

DECOMPRESS_TASK_TABLE = os.getenv("DecompressTaskTable")

EFS_MOUNT_POINT = os.getenv("EFSMountPath")
CHUNK_SIZE = 100

db = boto3.resource('dynamodb')
table = db.Table(DECOMPRESS_TASK_TABLE)


def lambda_handler(event, context):
    print(event)

    file_url = event["file_url"]
    id_token = event["id_token"]
    project_id = event["project_id"]
    project_name = event["project_name"]
    type_method = event["type_method"]
    task_id = event["task_id"]
    s3_prefix = event["s3_prefix"]
    identity_id = event["identity_id"]

    response = table.get_item(
        Key={"task_id": task_id,
             "identity_id": identity_id},
        ProjectionExpression="destination_dir"
    )
    print(response)
    destination_dir = response["Item"].get("destination_dir")

    glob_pattern = os.path.join(EFS_MOUNT_POINT, destination_dir, "*")
    all_files = glob.glob(glob_pattern)
    # get absolute path on EFS
    all_files = list(map(lambda x: os.path.join(destination_dir, os.path.basename(x)), all_files))
    file_chunks = []
    for size in range(0, len(all_files), CHUNK_SIZE):
        file_chunks.append(all_files[size:size + CHUNK_SIZE])

    print("succeed")
    return {
        "file_url": file_url,
        "id_token": id_token,
        "project_id": project_id,
        "project_name": project_name,
        "type_method": type_method,
        "file_chunks": file_chunks,
        "task_id": task_id,
        "s3_prefix": s3_prefix,
        "destination_dir": destination_dir
    }
