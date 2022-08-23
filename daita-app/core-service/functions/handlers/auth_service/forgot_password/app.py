from email import header, message
import os
from datetime import datetime
from http import HTTPStatus

import boto3
import json
from config import *
from error_messages import *
from verify_captcha import *
from custom_mail import *
from response import generate_response, error_response
from lambda_base_class import LambdaBaseClass
from utils import *

USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']

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

    for _, data in enumerate(response['Users']):
        if data['Username'] == user:
            for info in data['Attributes']:
                if info['Name'] == 'email':
                    return info['Value']
    return None


class ForgotPasswordClass(LambdaBaseClass):

    def __init__(self) -> None:
        super().__init__()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.username = body["username"]
        self.captcha = body["captcha"]

    def handle(self, event, context):

        self.parser(event)

        try:
            verify_captcha(self.captcha)
        except Exception as exc:
            raise Exception(MessageCaptchaFailed) from exc

        try:
            response = cog_provider_client.admin_get_user(
                UserPoolId=USERPOOLID,
                Username=self.username
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
                message=MessageUserVerifyConfirmCode,
                headers=RESPONSE_HEADER
            )
        mail = getMail(self.username)
        try:
            AddTriggerCustomMail({
                'lambda_name': os.environ['INVOKE_MAIL_LAMBDA'],
                'region': REGION,
                'user': self.username,
                'mail': mail,
                'subject': 'Your email confirmation code',
                'confirm_code_Table': os.environ['TABLE_CONFIRM_CODE']
            })
        except Exception as e:
            print(e)
            return generate_response(
                message=MessageForgotPasswordSuccessfully,
                headers=RESPONSE_HEADER,
                error=True
            )

        return generate_response(
            message=MessageForgotPasswordSuccessfully,
            headers=RESPONSE_HEADER
        )


@error_response
def lambda_handler(event, context):
    return ForgotPasswordClass().handle(event=event, context=context)
