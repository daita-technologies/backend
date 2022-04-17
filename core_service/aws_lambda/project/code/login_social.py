from email import header
import os
import json
import logging
import time
from datetime import datetime
from http import HTTPStatus
import os
import boto3
import cognitojwt
from utils import create_secret_hash, aws_get_identity_id
from urllib.parse import urlparse , quote

from error import *
from response import *
from config import *

import requests
import base64
import urllib.parse
from urllib.parse import urlencode
ACCESS_TOKEN_EXPIRATION = 24 * 60 * 60
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
endpoint = 'https://devdaitaloginsocial.auth.us-east-2.amazoncognito.com/oauth2/token'
client_id = '4cpbb5etp3q7grnnrhrc7irjoa'
def getRedirectURI():
    return 'https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/auth/login_social'
    


#############################################################################################################
def getCredentialsForIdentity(token_id):
    PROVIDER = f'cognito-idp.{REGION}.amazonaws.com/{USERPOOLID}'
    responseIdentity = aws_get_identity_id(token_id)

    credentialsResponse = cog_identity_client.get_credentials_for_identity(
                IdentityId=responseIdentity,
                Logins ={ 
                    PROVIDER: token_id
    })
      
    return {
        'secret_key': credentialsResponse['Credentials']['SecretKey'],
        'session_key': credentialsResponse['Credentials']['SessionToken'],
        'credential_token_expires_in':credentialsResponse['Credentials']['Expiration'].timestamp() * 1000,
        'access_key': credentialsResponse['Credentials']['AccessKeyId'],
        'identity_id':responseIdentity
    }
#############################################################################################################################################################
def Oauth2(code):
    params = {"code": code, "grant_type": "authorization_code", "redirect_uri": getRedirectURI(),'client_id':client_id,'scope':'email+openid+phone+profile'}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = urlencode(params)
    result = requests.post(endpoint, data=data, headers=headers)
    return result
##############################################################################################################################################3
@error_response
def lambda_handler(event, context):
    print(event,type(event))
    param = event['queryStringParameters']
    try:
        code = param['code']
    except Exception as e:
        print(e)
        raise Exception(e)
    if 'state' in param:
        path = base64.b64decode(param['state']).decode('utf-8')
    else: 
        path = 'http://localhost:3000/login'
    mapping ={
        'token' :'',
        'resfresh_token':'',
        'access_key':  '',
        'session_key':      '',
        'id_token':       '',
        'credential_token_expires_in':   '',
        'token_expires_in':'',
        'secret_key':               '',
        'identity_id': '',
        'username': '',
        'code': code
    }
    location = path + '?'+ urlencode(mapping,doseq=True)
    headers = {"Location":location,	"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT"}
    return {
        "statusCode": 302,
        "headers": headers,
        "body":'',
        "isBase64Encoded": False
    }