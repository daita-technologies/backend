import os
import json
import boto3
from response import *

lambda_mapper = {
    'create': os.environ['PRJ_CREATE_SAMPLE'],
    'download_create': os.environ['PRJ_DOWNLOAD_CREATE'],
    'download_update': os.environ['PRJ_DOWNLOAD_UPDATE'],
    'info': os.environ['PRJ_INFO'],
    'list': os.environ['PRJ_LIST'],
    'list_data': os.environ['PRJ_LIST_DATA'],
    'list_info': os.environ['PRJ_LIST_INFO'],
    'create_sample': os.environ['PRJ_SAMPLE'],
    'update_info': os.environ['PRJ_UPDATE_INFO'],
    'upload_check': os.environ['PRJ_UPDATE_CHECK'],
    'upload_update': os.environ['PRJ_UPLOAD_UPDATE']
}


def invokeLambda(info, lambdaFunc):
    lambdaInvokeClient = boto3.client('lambda')
    lambdaInvokeReq = lambdaInvokeClient.invoke(
        FunctionName=lambdaFunc,
        Payload=json.dumps({'body': info}),
        InvocationType="RequestResponse",
    )
    payload = json.loads(lambdaInvokeReq['Payload'].read())
    body = json.loads(payload['body'])
    return body


def lambda_handler(event, context):
    rawPath = event['rawPath']
    funcString = rawPath.split('/')[-1]
    if lambda_mapper.get(funcString, None) is None:
        return generate_response(error=True,
                                 message="Not Found!",
                                 data={},
                                 headers=RESPONSE_HEADER,
                                 )
    lambdaNameInvoke = str(lambda_mapper[funcString])
    body = event['body']
    try:
        response = invokeLambda(info=body, lambdaFunc=lambdaNameInvoke)
    except Exception as e:
        print(e)
        return generate_response(
            message=str(e),
            data={},
            headers=RESPONSE_HEADER,
            error=True
        )
    return response
