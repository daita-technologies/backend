import os
import json
import boto3
from response import *
from config import *

from models.generate_daita_upload_token import GenerateDaitaUploadTokenModel
from models.project_sum_model import ProjectSumModel

generate_daita_upload_token_model = GenerateDaitaUploadTokenModel(
    os.environ['T_GEN_DAITA_UPLOAD_TOKEN'])
project_sum_model = ProjectSumModel(os.environ["TABLE_PROJECT_SUM"])
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


def invokeUploadCheck(info):
    lambdaInvokeClient = boto3.client('lambda')
    lambdaInvokeReq = lambdaInvokeClient.invoke(
        FunctionName='staging-project-upload-check',
        Payload=json.dumps({'body': info}),
        InvocationType="RequestResponse",
    )


def generate_presigned_url(object_keyname, expired=3600):
    reponse = s3.generate_presigned_post(
        Bucket=bucket,
        Key=object_keyname,
        ExpiresIn=expired
    )
    return reponse


def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        filenames = body['filenames']
        daita_token = body['daita_token']
        ls_object_info = body['ls_object_info']
    except Exception as e:
        print(e)
        return generate_response(
            message=str(e),
            data={},
            headers=RESPONSE_HEADER,
            error=True)
    data = {}
    info = generate_daita_upload_token_model.query_by_token(token=daita_token)
    if info is None:
        return generate_response(
            message="Token is expired, please get another token!",
            data={},
            headers=RESPONSE_HEADER,
            error=True)
    identity_id = info['identity_id']
    project_id = info['project_id']
    id_token = info['id_token']
    project_name = info['project_name']
    # check number of images in project
    prjSumAllResp = project_sum_model.get_item(
        project_id=project_id, type_data='ORIGINAL')

    if prjSumAllResp is None:
        return generate_response(
            message="Something wrong with your project, Please check again!",
            data={},
            headers=RESPONSE_HEADER,
            error=True)

    countSumAllPrj = int(prjSumAllResp['count'])
    if countSumAllPrj + len(filenames) >= 1000:
        return generate_response(
            message="Limited",
            data={},
            headers=RESPONSE_HEADER,
            error=True)

    folder = os.path.join(identity_id, project_id)

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
