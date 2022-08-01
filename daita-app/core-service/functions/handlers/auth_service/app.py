import os
import json
import boto3
from response import *

lambda_mapper = {
    'user_signup': os.environ['SIGNUP_LAMBDA'],
    'user_login': os.environ['LOGIN_LAMBDA'],
    'auth_confirm': os.environ['AUTHCONFIRM_LAMBDA'],
    'resend_confirmcode': os.environ['RESENDCODEAUTH_LAMBDA'],
    'confirm_code_forgot_password': os.environ['CONFIRMCODEFORGOTPASSWORD_LAMBDA'],
    'forgot_password': os.environ['FORGOTPASSWORD_LAMBDA'],
    'refresh_token': os.environ['RERRESHTOKEN_LAMBDA']
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
