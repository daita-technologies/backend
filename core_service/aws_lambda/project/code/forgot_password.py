from email import header, message
import os
from datetime import datetime
from http import HTTPStatus

import boto3
import json
from config import *
from error import *
from verify_captcha import *
from custom_mail import *
from response import generate_response, error_response


cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Credentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
def getMail(user):
    response = cog_provider_client.list_users(
        UserPoolId=USERPOOLID
    )
    # info_user =  list(filter(lambda x : x['Username'] == user,response['Users']))

    for _ , data in enumerate(response['Users']):
        if data['Username'] == user:
            for  info in data['Attributes']:
                if info['Name'] == 'email':
                    return info['Value']
    return None

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
    if not is_email_verified:
        return generate_response(
            message= MessageUserVerifyConfirmCode,
            headers=RESPONSE_HEADER
        )
    mail = getMail(username)
    AddTriggerCustomMail({
        'region':REGION,
        'user':username,
        'mail':mail,
        'subject':'Your email confirmation code'
    })

    return generate_response(
        message=MessageForgotPasswordSuccessfully,
        headers=RESPONSE_HEADER
    )
    
        
    