import os
import json
from pathlib import Path
import boto3


s3_client = boto3.client('s3')
S3_BUCKET = os.getenv("S3_BUCKET")
EFS_ROOT = Path(os.getenv("EFSMountPath"))


def lambda_handler(event, context):
    file_chunk = event["file_chunk"]
    workdir = event["workdir"]

    files = []
    for file_info in file_chunk:
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
