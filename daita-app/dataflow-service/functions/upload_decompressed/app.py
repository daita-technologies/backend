import os
import json
import glob
from pathlib import Path
from hashlib import md5

import boto3


EFS_MOUNT_POINT = os.getenv("EFSMountPath")
BUCKET = os.getenv("S3BucketName")

efs_mount_point = Path(EFS_MOUNT_POINT)
s3_client = boto3.client('s3')
db_client = boto3.client('dynamodb')

table_data_org = db_client.Table("data_original")


def get_file_md5_hash(file):
    with open(file, "rb") as rstr:
        return md5(rstr.read()).hexdigest()


def lambda_handler(event, context):
    print(event)

    file_chunk = event["file_chunk"]
    id_token = event["id_token"]
    project_id = event["project_id"]
    project_name = event["project_name"]
    type_method = event["type_method"]
    s3_prefix = event["s3_prefix"]

    print(file_chunk)
    ls_object_info = []
    for file_ in file_chunk:
        file_path = efs_mount_point.joinpath(file_)
        filename = file_path.name
        file_path = str(file_path)
        # s3_prefix is include bucket name so we have to extract the relative path
        object_name = str(Path(s3_prefix, filename).relative_to(BUCKET))
        response = s3_client.upload_file(file_path, BUCKET, object_name)
        print(file_path, object_name, response)
        file_size = os.stat(file_path).st_size

        ### check data exist in DB
        response = table_data_org.get_item(
            Key={
                'project_id': project_id,
                'filename': filename,
            },
            ProjectionExpression= 'size'
        )
        if response.get('Item', None) is None:
            size_old = 0
        else:
            size_old = response['Item']['size']

        # generate ls_object_info        
        ls_object_info.append({
            "filename": filename,
            "gen_id": "",
            "hash": get_file_md5_hash(file_path),
            "is_ori": True,
            "s3_key": os.path.join(BUCKET, object_name),
            "size": file_size,
            "size_old": size_old
        })

    payload = {
        "id_token": id_token,
        "project_id": project_id,
        "project_name": project_name,
        "ls_object_info": ls_object_info,
        "type_method": type_method,
    }

    print("succeed")
    return {
        "body": json.dumps(payload),
        "file_chunk": file_chunk
    }
