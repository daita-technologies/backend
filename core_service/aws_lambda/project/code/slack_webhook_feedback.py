import requests
import json
import os
import json
from datetime import datetime
from http import HTTPStatus
import os
import boto3
import cognitojwt
from error import *
from response import *
from config import *
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
    token = authorization_header.replace('Bearer ','')
    if not len(authorization_header):
        raise Exception(MessageMissingAuthorizationHeader)
    try:
        body = json.loads(event['body'])
        text = body['text']
    except Exception as e:
        print(e)
        raise Exception(MessageUnmarshalInputJson)
    try:
        username = claimsToken(token,'username')
    except Exception as e:
        raise e
    payload ={"channel":CHANNELWEBHOOK,
    "username":username,
    "text":text,
    "icon_emoji":":ghost:"}
    req  = requests.post(
        WEBHOOK,json=payload
    )
    #MessageSendFeedbackFailed = "Send feeback failed"
    # MessageSendFeedbackSuccessfully = "send feedback successfully"
    if req.status_code != 200:
        return generate_response(
            message=MessageSendFeedbackFailed,
            data={},
            headers=RESPONSE_HEADER
        )
    return generate_response(
            message=MessageSendFeedbackSuccessfully,
            data={},
            headers=RESPONSE_HEADER
        )

