import os
import json
import boto3
from error import *
from response import *
from config import *
s3 = boto3.client('s3')
bucket = os.environ['BUCKET_NAME']
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


def invokeUploadUpdateFunc(info):
    lambdaInvokeClient = boto3.client('lambda')
    lambdaInvokeReq = lambdaInvokeClient.invoke(
        FunctionName='staging-project-upload-update',
        Payload=json.dumps({'body': info}),
        InvocationType="RequestResponse",
    )
    print(lambdaInvokeReq['Payload'].read())


def invokeUploadCheck(info):
    lambdaInvokeClient = boto3.client('lambda')
    lambdaInvokeReq = lambdaInvokeClient.invoke(
        FunctionName='staging-project-upload-check',
        Payload=json.dumps({'body': info}),
        InvocationType="RequestResponse",
    )
    print(lambdaInvokeReq['Payload'].read())


def generate_presigned_url(object_keyname, expired=3600):
    reponse = s3.generate_presigned_post(
        Bucket=bucket,
        Key=object_keyname,
        ExpiresIn=expired
    )
    return reponse


@error_response
def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        filenames = body['filenames']
        daita_token = body['daita_token']
        ls_object_info = body['ls_object_info']
    except Exception as e:
        print(e)
        return generate_response(
            message=MessageAuthenFailed,
            data={},
            headers=RESPONSE_HEADER,
            error=True)
    folder = os.path.join(identity, project_id)
    data = {}
    for it in filenames:
        basename = os.path.basename(it)
        data[basename] = generate_presigned_url(
            object_keyname=os.path.join(folder, basename))
    ls_filename = []
    for objectS3 in ls_object_info:
        objectS3['s3_key'] = os.path.join(
            bucket, os.path.join(folder, objectS3['filename']))
        ls_filename.append(objectS3['filename'])
    invokeUploadUpdateFunc(json.dumps({
        "id_token": id_token,
        "project_id": project_id,
        "project_name": project_name,
        "ls_object_info":  ls_object_info
    }))
    invokeUploadCheck(json.dumps(
        {
            "id_token": id_token,
            "ls_filename": ls_filename,
            "project_id": project_id
        }
    ))
    return generate_response(
        message="Generate presign Url S3 successfully",
        data=data,
        headers=RESPONSE_HEADER
    )
