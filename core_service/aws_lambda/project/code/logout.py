from email import header
import os
import json
import logging
import requests
from datetime import datetime
from http import HTTPStatus
import os
import boto3
import cognitojwt
from error import *
from response import *
from config import *
from urllib.parse import urlencode
from eventID import EventUserLogout, CheckEventUserLogin, get_code_oauth2_cognito

cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
endpoint ='https://auth.daita.tech/logout'
def getRedirectURI():
    return 'https://app.daita.tech/login'

def logoutOauth2(code):
    newendpoint = 'https://auth.daita.tech/logout?'+'response_type='+code+ \
                '&redirect_uri=https://app.daita.tech/login&client_id=4cpbb5etp3q7grnnrhrc7irjoa&scope=openid+profile+aws.cognito.signin.user.admin'
    result = requests.get(newendpoint)
    return result

def claimsToken(jwt_token,field):
    """
    Validate JWT claims & retrieve user identifier
    """
    token = jwt_token.replace("Bearer ", "")
    print(token)
    try:
        verified_claims = cognitojwt.decode(
            token, REGION, USERPOOLID
        )
    except Exception as e:
        print(e)
        raise e

    return verified_claims.get(field)

@error_response
def lambda_handler(event, context):
    headers = event['headers']['Authorization']
    authorization_header = headers
    if not len(authorization_header):
        raise Exception(MessageMissingAuthorizationHeader)
    try:
        sub = claimsToken(authorization_header,'sub')
        username = claimsToken(authorization_header,'username')
    except Exception as e:
        raise e
    code = None 
    data = {}
    if CheckEventUserLogin(sub):
        if 'github' in username or 'google' in username:
            code = get_code_oauth2_cognito(sub)
            data['code'] = code
        EventUserLogout(sub)

    return generate_response(
            message= MessageLogoutSuccessfully,
            headers=RESPONSE_HEADER,
            data = data
        )