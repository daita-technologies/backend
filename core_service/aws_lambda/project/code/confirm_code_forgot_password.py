import re

import boto3
import json
from config import *
from error import *
from custom_mail import *
from response import generate_response, error_response


cog_provider_client = boto3.client("cognito-idp")
RESPONSE_HEADER = {
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\^$*.\[\]{}\(\)?\-\"!@#%&\/,><\':;|_~`])\S{8,99}$"


@error_response
def lambda_handler(event, context):
    """
    https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-concepts.html#gettingstarted-concepts-event
    https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    """
    # get params REFRESH_TOKEN passed by FE in event body
    try:
        body = json.loads(event["body"])
        username = body["username"]
        password = body["password"]
        confirm_code = body["confirm_code"]
    except Exception as exc:
        raise Exception(MessageUnmarshalInputJson) from exc

    try:
        DeleteConfirmCode({"region": REGION, "user": username, "code": confirm_code})
    except Exception as e:
        raise Exception(e)

    if not re.match(PASSWORD_REGEX, password):
        AddInsertConfirmCode(info={"user": username, "confirm_code": confirm_code})
        raise Exception(MessageInvalidPassword)

    try:
        response = cog_provider_client.admin_set_user_password(
            UserPoolId=USERPOOLID, Username=username, Password=password, Permanent=True
        )
        print(response)
    except Exception as exc:
        print(exc)
        AddInsertConfirmCode(info={"user": username, "confirm_code": confirm_code})
        raise Exception(MessageForgotPasswordConfirmcodeFailed) from exc

    return generate_response(
        message=MessageForgotPasswordConfirmcodeSuccessfully, headers=RESPONSE_HEADER
    )
