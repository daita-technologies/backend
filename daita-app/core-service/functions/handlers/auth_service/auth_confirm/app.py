from cmath import inf
import os
import json
import logging
from http import HTTPStatus
import os
import boto3
from dataclasses import dataclass
import re
from utils import *
from error_messages import *
from response import *
from config import *
from custom_mail import *
from datetime import datetime

USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')


@error_response
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        username = body['username']
        confirmCode = body['confirm_code']
    except Exception as e:
        print("error ", e)
        return generate_response(
            message=MessageUnmarshalInputJson,
            data={},
            headers=RESPONSE_HEADER
        )
    try:
        DeleteConfirmCode({
            'region': REGION,
            'user': username,
            'code': confirmCode,
            'confirm_code_Table': os.environ['TABLE_CONFIRM_CODE']
        })
    except Exception as e:
        raise Exception(e)
    _ = cog_provider_client.admin_confirm_sign_up(
        UserPoolId=USERPOOLID,
        Username=username
    )

    _ = cog_provider_client.admin_update_user_attributes(
        UserPoolId=USERPOOLID,
        Username=username,
        UserAttributes=[
            {
                'Name': 'email_verified',
                'Value': 'true'
            },
        ])
    return generate_response(message="Email successfully confirmed", data={},
                             headers=RESPONSE_HEADER
                             )
