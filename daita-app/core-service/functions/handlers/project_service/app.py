import os
import json
import boto3
from response import *

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
    return {}