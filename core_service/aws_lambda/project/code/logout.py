from email import header
import os
import json
import logging
from datetime import datetime
from http import HTTPStatus
import os
import boto3
import cognitojwt
from error import *
from response import *
from config import *
from eventID import EventUserLogout, CheckEventUserLogin

cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


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
    except Exception as e:
        raise e
    if CheckEventUserLogin(sub):
        EventUserLogout(sub)
    # else:
    #     return generate_response(
    #         message= MessageErrorUserdoesnotlogin,
    #         headers=RESPONSE_HEADER,
    #         error = True,
    #     )
    return generate_response(
            message= MessageLogoutSuccessfully,
            headers=RESPONSE_HEADER
        )