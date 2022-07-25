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
from custom_mail import *
from datetime import datetime


def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()


USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
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


@error_response
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        username = body['username']
        mail = getMail(username)
    except Exception as e:
        print(e)
        raise Exception(e)

    ResendCodeConfirm({
        'region': REGION,
        'user': username,
        'mail': mail,
        'subject': 'Your email confirmation code'
    })
    return generate_response(
        message=MessageResendEmailConfirmCodeSuccessfully,
        data={},
        headers=RESPONSE_HEADER
    )
