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
from verify_captcha import *

from datetime import datetime


def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()


USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
cog_provider_client = boto3.client("cognito-idp")
cog_identity_client = boto3.client("cognito-identity")
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\^$*.\[\]{}\(\)?\-\"!@#%&\/,><\':;|_~`])\S{8,99}$"

TableUser = os.environ['TBL_USER']


class User(object):
    def __init__(self):
        self.db_client = boto3.resource("dynamodb", region_name=REGION)
        self.TBL = TableUser

    def create_item(self, info):
        self.db_client.Table(self.TBL).put_item(
            Item={
                "ID": info["ID"],
                "username": info["username"],
                "role": "normal",
                "status": "deactivate",
                "create_at": convert_current_date_to_iso8601(),
            }
        )


def checkInvalidUserRegister(user, mail):
    response = cog_provider_client.list_users(UserPoolId=USERPOOLID)
    info_user = list(
        filter(lambda x: x["Username"] == user, response["Users"]))
    if len(info_user):
        return False, True
    for _, data in enumerate(response["Users"]):
        for info in data["Attributes"]:
            if info["Name"] == "email" and info["Value"] == mail:
                return True, False
    return True, True


@error_response
def lambda_handler(event, context):

    try:
        body = json.loads(event["body"])
        username = body["username"]
        mail = body["email"]
        password = body["password"]
        captcha = body["captcha"]
    except Exception as e:
        print(e)
        raise Exception(e)

    try:
        verify_captcha(captcha)
    except Exception as exc:
        raise Exception(MessageCaptchaFailed) from exc

    if not re.match(PASSWORD_REGEX, password):
        raise Exception(MessageInvalidPassword)
    checkUsername, checkemail = checkInvalidUserRegister(username, mail)

    if not checkUsername:
        raise Exception(MessageSignUpUsernameInvalid)
    elif not checkemail:
        raise Exception(MessageSignUPEmailInvalid)

    try:
        respUserSignUp = cog_provider_client.sign_up(
            ClientId=CLIENTPOOLID,
            Username=username,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": mail}],
        )
    except Exception as e:
        print(e)
        raise Exception(MessageSignUpFailed)

    model = User()
    try:
        model.create_item(
            {"ID": respUserSignUp["UserSub"], "username": username})
    except Exception as e:
        print(e)
        raise Exception(MessageSignUpFailed)
    try:
        AddTriggerCustomMail(
            {
                'lambda_name': os.environ['INVOKE_MAIL_LAMBDA'],
                'region': REGION,
                'user': username,
                'mail': mail,
                'subject': "Your email confirmation code",
                'confirm_code_Table': os.environ['TBL_CONFIRM_CODE']
            }
        )
    except Exception as e:
        return generate_response(
        message=str(e),
        data={},
        headers=RESPONSE_HEADER,
        error= True
    )
    return generate_response(
        message="Sign up for user {} was successful.".format(username),
        data={},
        headers=RESPONSE_HEADER,
    )
