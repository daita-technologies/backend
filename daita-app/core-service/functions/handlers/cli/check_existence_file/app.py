import os
import json
import boto3
from response import *
from config import *

from models.generate_daita_upload_token import GenerateDaitaUploadTokenModel

generate_daita_upload_token_model = GenerateDaitaUploadTokenModel(
    os.environ['T_GEN_DAITA_UPLOAD_TOKEN'])


def invokeUploadUpdateFunc(info):
    lambdaInvokeClient = boto3.client('lambda')
    lambdaInvokeReq = lambdaInvokeClient.invoke(
        FunctionName=os.environ['LAMBDA_UPDATE_CHECK'],
        Payload=json.dumps({'body': info}),
        InvocationType="RequestResponse",
    )
    payload = json.loads(lambdaInvokeReq['Payload'].read())
    body = json.loads(payload['body'])
    return body


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        daita_token = body['daita_token']
        ls_filename = body['ls_filename']
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

    project_id = info['project_id']
    id_token = info['id_token']
    payloadInfo = {
        'project_id': project_id,
        'id_token': id_token,
        'ls_filename': ls_filename
    }
    return invokeUploadUpdateFunc(json.dumps(payloadInfo))
