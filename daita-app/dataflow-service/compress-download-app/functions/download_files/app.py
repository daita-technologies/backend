import os
import json
from pathlib import Path
import boto3


s3_client = boto3.client('s3')
S3_BUCKET = os.getenv("S3_BUCKET")
EFS_ROOT = Path(os.getenv("EFSMountPath"))


def lambda_handler(event, context):
    file_chunk_index = event["file_chunk"]
    workdir = event["workdir"]
    bucket = event["bucket"]
    s3_key_path = event ["s3_key_path"]

    ### read data from s3 and get data with index        
    resultS3 = s3_client.get_object(Bucket=bucket, Key=s3_key_path)
    ls_data = json.loads(resultS3["Body"].read().decode())
    data = ls_data[file_chunk_index]

    for file_info in data:
        s3_key = file_info["s3_key"]
        type_method = file_info["type_method"]
        filename = os.path.basename(s3_key)
        destdir = EFS_ROOT.joinpath(workdir, type_method)
        destfile = destdir.joinpath(filename)
        destfile_info = destfile.with_suffix(".json")

        key = s3_key.replace(f"{S3_BUCKET}/", '')
        destdir.mkdir(parents=True, exist_ok=True)
        with destfile.open("wb") as wstr:
            s3_client.download_fileobj(S3_BUCKET, key, wstr)
        with destfile_info.open("w") as wstr:
            json.dump(file_info, wstr)
