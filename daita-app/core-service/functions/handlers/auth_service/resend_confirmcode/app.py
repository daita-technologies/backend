from cmath import inf
import os
import json
import logging
from http import HTTPStatus
import os
import boto3
from dataclasses import dataclass
import re

from error_messages import *
from response import *
from config import *
from custom_mail import *
from datetime import datetime
from lambda_base_class import LambdaBaseClass


def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()


USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']

cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
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


class ResendConfirmCodeClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.username = body['username']
        self.mail = getMail(self.username)

    def handle(self, event, context):
        self.parser(event)
        ResendCodeConfirm({
            'lambda_name': os.environ['INVOKE_MAIL_LAMBDA'],
            'region': REGION,
            'user': self.username,
            'mail': self.mail,
            'subject': 'Your email confirmation code',
            'confirm_code_Table': os.environ['TABLE_CONFIRM_CODE']

        })
        return generate_response(
            message=MessageResendEmailConfirmCodeSuccessfully,
            data={},
            headers=RESPONSE_HEADER
        )


@error_response
def lambda_handler(event, context):
    return ResendConfirmCodeClass.handle(event=event, context=context)
