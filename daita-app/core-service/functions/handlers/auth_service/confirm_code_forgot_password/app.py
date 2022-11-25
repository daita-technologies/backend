import re
import os
import boto3
import json
from config import *
from error_messages import *
from custom_mail import *
from utils import *
from response import generate_response, error_response
from lambda_base_class import LambdaBaseClass

USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']

cog_provider_client = boto3.client('cognito-idp')
RESPONSE_HEADER = {
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\^$*.\[\]{}\(\)?\-\"!@#%&\/,><\':;|_~`])\S{8,99}$"


class ConfirmCodeForgotPasswordClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.username = body["username"]
        self.password = body["password"]
        self.confirm_code = body["confirm_code"]

    def handle(self, event, context):
        self.parser(event)
        try:
            DeleteConfirmCode({
                'region': REGION,
                'user': self.username,
                'code': self.confirm_code,
                'confirm_code_Table': os.environ['TABLE_CONFIRM_CODE']
            })
        except Exception as e:
            raise Exception(e)

        if not re.match(PASSWORD_REGEX, self.password):
            AddInsertConfirmCode(
                info={'user': self.username, 'confirm_code': self.confirm_code, 'confirm_code_Table': os.environ['TABLE_CONFIRM_CODE']})
            raise Exception(MessageInvalidPassword)

        try:
            response = cog_provider_client.admin_set_user_password(
                UserPoolId=USERPOOLID, Username=self.username, Password=self.password, Permanent=True)
            print(response)
        except Exception as exc:
            print(exc)
            AddInsertConfirmCode(
                info={'user': self.username, 'confirm_code': self.confirm_code, 'confirm_code_Table': os.environ['TABLE_CONFIRM_CODE']})
            raise Exception(MessageForgotPasswordConfirmcodeFailed) from exc

        return generate_response(
            message=MessageForgotPasswordConfirmcodeSuccessfully,
            headers=RESPONSE_HEADER
        )


@error_response
def lambda_handler(event, context):
    return ConfirmCodeForgotPasswordClass().handle(event=event, context=context)
