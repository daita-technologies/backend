import os
from datetime import datetime
from http import HTTPStatus

import boto3
import json
from config import *
from error import *
from verify_captcha import *
from response import generate_response, error_response


cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Credentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


@error_response
def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        username = body["username"]
        captcha = body["captcha"]
    except Exception as exc:
        raise Exception(MessageUnmarshalInputJson) from exc

    try:
        verify_captcha(captcha)
    except Exception as exc:
        raise Exception(MessageCaptchaFailed) from exc

    try:
        response = cog_provider_client.admin_get_user(
            UserPoolId=USERPOOLID,
            Username=username
        )
    except Exception as exc:
        print(exc)
        raise Exception(MessageForgotPasswordUsernotExist) from exc

    is_email_verified = True
    for it in response['UserAttributes']:
        if it['Name'] == 'email_verified' and it['Value'] == 'false':
            is_email_verified = False
            break
    if is_email_verified:
        response = cog_provider_client.forgot_password(
            ClientId=CLIENTPOOLID,
            Username=username
        )
        return generate_response(
            message=MessageForgotPasswordSuccessfully,
            headers=RESPONSE_HEADER
        )

    return generate_response(
        message=MessageForgotPasswordFailed,
        headers=RESPONSE_HEADER
    )
