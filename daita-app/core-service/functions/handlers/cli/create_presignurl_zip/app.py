import os
import json
import boto3
from response import *
from config import *
from models.generate_daita_upload_token import GenerateDaitaUploadTokenModel

s3 = boto3.client('s3')
bucket = os.environ['BUCKET_NAME']
generate_daita_upload_token_model = GenerateDaitaUploadTokenModel(
    os.environ['T_GEN_DAITA_UPLOAD_TOKEN'])


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
        daita_token = body['daita_token']
        is_zip = body['is_zip']
    except Exception as e:
        print(e)
        return generate_response(
            message=str(e),
            data={},
            headers=RESPONSE_HEADER,
            error=True)

    info = generate_daita_upload_token_model.query_by_token(token=daita_token)

    if info is None:
        return generate_response(
            message="Token is expired, please get another token!",
            data={},
            headers=RESPONSE_HEADER,
            error=True)

    identity_id = info['identity_id']
    project_id = info['project_id']
    folder = os.path.join(identity_id, project_id)
    data = {}
    basename = os.path.basename(filename)

    if is_zip == False:
        data['presign_url'] = generate_presigned_url(
            object_keyname=os.path.join(folder, basename))
        data['s3_uri'] = f's3://{bucket}/{identity_id}/{project_id}/{basename}'
        return  generate_response(
        message="Generate presign Url S3 successfully",
        data=data,
        headers=RESPONSE_HEADER,
        error=False
    )

    folder = os.path.join('tmp', folder)
    data['presign_url'] = generate_presigned_url(
        object_keyname=os.path.join(folder, basename))
    data['s3_uri'] = f's3://{bucket}/tmp/{identity_id}/{project_id}/{basename}'

    return generate_response(
        message="Generate presign Url S3 successfully",
        data=data,
        headers=RESPONSE_HEADER,
        error=False
    )
