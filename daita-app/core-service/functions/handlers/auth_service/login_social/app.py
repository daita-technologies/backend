from email import header
import os
import json
import logging
import time
from datetime import datetime
from http import HTTPStatus
import os
import boto3

from error_messages import *
from response import *
from config import *
from lambda_base_class import LambdaBaseClass

import base64
from urllib.parse import urlencode
ACCESS_TOKEN_EXPIRATION = 24 * 60 * 60
USERPOOLID = os.environ['COGNITO_USER_POOL']
IDENTITY_POOL = os.environ['IDENTITY_POOL']

cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')


@error_response
def lambda_handler(event, context):
    param = event['queryStringParameters']
    try:
        code = param['code']
    except Exception as e:
        print(e)
        if 'error_description' in param:
            location = LOCATION
            headers = {"Location": location,
                       "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT"}
            return {
                "statusCode": 302,
                "headers": headers,
                "body": '',
                "isBase64Encoded": False
            }
        raise Exception(e)

    if 'state' in param:
        path = base64.b64decode(param['state']).decode('utf-8')
    else:
        path = 'http://localhost:3000/login'
    mapping = {
        'token': '',
        'resfresh_token': '',
        'access_key':  '',
        'session_key':      '',
        'id_token':       '',
        'credential_token_expires_in':   '',
        'token_expires_in': '',
        'secret_key':               '',
        'identity_id': '',
        'username': '',
        'code': code
    }
    location = path + '?' + urlencode(mapping, doseq=True)
    headers = {"Location": location,
               "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT"}
    return {
        "statusCode": 302,
        "headers": headers,
        "body": '',
        "isBase64Encoded": False
    }


class LoginSocialClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.code = body['code']

    def handle(self, event, context):
        param = event['queryStringParameters']
        try:
            self.parser(param)
        except Exception as e:
            if 'error_description' in param:
                location = LOCATION
                headers = {"Location": location,
                           "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT"}
                return {
                    "statusCode": 302,
                    "headers": headers,
                    "body": '',
                    "isBase64Encoded": False
                }
            raise Exception(e)

        if 'state' in param:
            path = base64.b64decode(param['state']).decode('utf-8')
        else:
            path = 'http://localhost:3000/login'
        mapping = {
            'token': '',
            'resfresh_token': '',
            'access_key':  '',
            'session_key':      '',
            'id_token':       '',
            'credential_token_expires_in':   '',
            'token_expires_in': '',
            'secret_key':               '',
            'identity_id': '',
            'username': '',
            'code': self.code
        }
        location = path + '?' + urlencode(mapping, doseq=True)
        headers = {"Location": location,
                   "Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT"}
        return {
            "statusCode": 302,
            "headers": headers,
            "body": '',
            "isBase64Encoded": False
        }


@error_response
def lambda_handler(event, context):
    return LoginSocialClass.handle(event=event, context=context)
