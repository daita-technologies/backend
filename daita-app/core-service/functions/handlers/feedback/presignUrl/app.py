import os
import json
import boto3
from response import *
from config import *
from identity_check import *
s3 = boto3.client('s3')
bucket = os.environ['BUCKET_NAME']


def generate_presigned_url(object_keyname, expired=3600):
    response = s3.generate_presigned_post(
        Bucket=bucket,
        Key=object_keyname,
        ExpiresIn=expired
    )
    return response


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        filename = body['filename']
        id_token = body['id_token']
    except Exception as e:
        print(e)
        return generate_response(
            message=str(e),
            data={},
            headers=RESPONSE_HEADER,
            error=True)
    try:
        identity_id = aws_get_identity_id(id_token)
    except Exception as e:
        print(e)
        return generate_response(
            message=str(e),
            data={},
            headers=RESPONSE_HEADER,
            error=True)
    data = {}
    folder = os.path.join('feedback', identity_id)
    basename = os.path.basename(filename)
    folder = os.path.join(folder, basename)
    data['presign_url'] = generate_presigned_url(
        object_keyname=folder)
    data['s3_uri'] = f's3://{bucket}/feedback/{identity_id}/{basename}'
    return generate_response(
        message='create presign url successfully!',
        data=data,
        headers=RESPONSE_HEADER,
        error=False
    )
