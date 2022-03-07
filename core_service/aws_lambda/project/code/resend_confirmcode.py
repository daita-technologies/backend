from cmath import inf
import os
import json
import logging
from http import HTTPStatus
import os
import boto3
from dataclasses import dataclass
import re 

from error import *
from response import *
from config import *
from datetime import datetime
def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


@error_response
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        username = body['username']
    except Exception as e:
        print(e)
        raise Exception(e)
    resqResendConfirmCode = cog_provider_client.resend_confirmation_code(
        ClientId=CLIENTPOOLID,
        Username= username,
    )
    print(resqResendConfirmCode)
    return generate_response(
            message=MessageResendEmailConfirmCodeSuccessfully,
            data={},
            headers=RESPONSE_HEADER
        )
