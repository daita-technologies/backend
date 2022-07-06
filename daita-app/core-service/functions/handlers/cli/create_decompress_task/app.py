import os
import json
import boto3
from response import *
from config import *
from models.generate_daita_upload_token import GenerateDaitaUploadTokenModel

generate_daita_upload_token_model = GenerateDaitaUploadTokenModel(
    os.environ['T_GEN_DAITA_UPLOAD_TOKEN'])


def invokeLambda(info):
    lambdaInvokeClient = boto3.client('lambda')
    lambdaInvokeReq = lambdaInvokeClient.invoke(
        FunctionName=str(os.environ['DECOMPRESS_LAMBDA_INVOKE']),
        Payload=json.dumps({'body': info}),
        InvocationType="RequestResponse",
    )
    payload = json.loads(lambdaInvokeReq['Payload'].read())
    body = json.loads(payload['body'])
    return body


def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        s3 = body['s3']
        daita_token = body['daita_token']
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
    info = json.dumps({
        'id_token': info['id_token'],
        'project_id': info['project_id'],
        'project_name': info['project_name'],
        'type_method': "ORIGINAL",
        'file_url': s3
    })
    responseInvokeLambda = invokeLambda(info)
    print(responseInvokeLambda)
    return generate_response(
        message="Create decompress task successfully!",
        data=responseInvokeLambda,
        headers=RESPONSE_HEADER,
        error=True)
