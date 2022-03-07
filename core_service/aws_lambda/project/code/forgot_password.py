import os
from datetime import datetime
from http import HTTPStatus

import boto3

from config import *
from error import *
from utils import verify_captcha
from response import generate_response, error_response


cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Credentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


@error_response
def lamdba_handler(event, context):
    try:
        username = event["username"]
        captcha = event["captcha"]
    except Exception as exc:
        raise Exception(MessageUnmarshalInputJson) from exc

    try:
        verify_captcha(captcha)
    except Exception as exc:
        raise Exception(MessageCaptchaFailed) from exc

    try:
        response = cog_provider_client.admin_get_user(
            UserPoolId=USERPOOLID,
            username=username
        )
    except cog_provider_client.meta.exceptions.UserNotFoundException as exc:
        raise Exception(MessageForgotPasswordUsernotExist) from exc

    is_email_verified =  bool(response["UserAttributes"]["email_verified"])
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
