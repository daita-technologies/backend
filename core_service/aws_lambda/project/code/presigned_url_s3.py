from email.mime import base
import os
import json
import boto3
from error import *
from response import *
from config import *

s3 = boto3.client("s3")
bucket = os.environ["BUCKET_S3"]
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


def generate_presigned_url(object_keyname, expired=3600):
    reponse = s3.generate_presigned_post(
        Bucket=bucket, Key=object_keyname, ExpiresIn=expired
    )
    return reponse


@error_response
def lambda_handler(event, context):

    try:
        body = json.loads(event["body"])
        filenames = body["filenames"]
        identity = body["identity"]
        project_id = body["project_id"]
    except Exception as e:
        print(e)
        return generate_response(
            message=MessageAuthenFailed, data={}, headers=RESPONSE_HEADER, error=True
        )
    folder = os.path.join(identity, project_id)
    data = {}
    for it in filenames:
        basename = os.path.basename(it)
        data[basename] = generate_presigned_url(
            object_keyname=os.path.join(folder, basename)
        )

    return generate_response(
        message="Generate presign Url S3 successfully",
        data=data,
        headers=RESPONSE_HEADER,
    )
