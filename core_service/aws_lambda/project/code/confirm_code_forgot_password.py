import re

import boto3

from config import *
from error import *
from response import generate_response, error_response


cog_provider_client = boto3.client('cognito-idp')
RESPONSE_HEADER = {
    "Access-Control-Allow-Credentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\^$*.\[\]{}\(\)?\-\"!@#%&\/,><\':;|_~`])\S{8,99}$"


@error_response
def lambda_handler(event, context):
    '''
    https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-concepts.html#gettingstarted-concepts-event
    https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    '''
    # get params REFRESH_TOKEN passed by FE in event body
    try:
        username = event["username"]
        password = event["password"]
        confirm_code = event["confirm_code"]
    except Exception as exc:
        raise Exception(MessageUnmarshalInputJson) from exc

    if not re.match(PASSWORD_REGEX, password):
        raise Exception(MessageInvalidPassword)

    try:
        # TODO: check logic to raise some exception from response body
        response = cog_provider_client.confirm_forgot_password(
            Username=username,
            Password=password,
            ConfirmationCode=confirm_code,
            ClientId=CLIENTPOOLID
        )
    except Exception as exc:
        raise Exception(MessageForgotPasswordConfirmcodeFailed) from exc

    return generate_response(
        message=MessageForgotPasswordConfirmcodeSuccessfully,
        headers=RESPONSE_HEADER
    )
