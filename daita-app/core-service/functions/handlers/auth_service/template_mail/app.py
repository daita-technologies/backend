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
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


def getMail(user):
    response = cog_provider_client.list_users(
        UserPoolId=USERPOOLID
    )
    for _, data in enumerate(response['Users']):
        if data['Username'] == user:
            for info in data['Attributes']:
                if info['Name'] == 'email':
                    return info['Value']
    return None


def claimsToken(jwt_token, field):
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
        verified_claims = {}

    return verified_claims.get(field)


@error_response
def lambda_handler(event, context):
    headers = event['headers']['Authorization']
    authorization_header = headers
    # authorization_header = {k.lower(): v for k, v in headers.items() if k.lower() == 'authorization'}
    if not len(authorization_header):
        raise Exception(MessageMissingAuthorizationHeader)
    username = claimsToken(authorization_header, 'username')
    mail = getMail(username)
    template = "<p>Hi,</p><p>{} has invited you to explore DAITA's recently launched " \
        "<a href=\"https://app.daita.tech\"style=\"text-decoration:none;color:inherit;border-bottom: solid 2px\">data augmentation platform</a>.</p> " \
        "<p>Building a platform that machine learning engineers and data scientists " \
        "really love is truly hard. But that's our ultimate ambition!</p> <p>Thus, your feedback" \
        " is greatly appreciated, as this first version will still be buggy and missing many features. Please send " \
        "all your thoughts, concerns, feature requests, etc. to <a href=\"mailto:contact@daita.tech?subject=DAITA%20Platform%20User%20Feedback\"\>contact@daita.tech</a> or simply reply to this e-mail. " \
        "Please be assured that all your feedback will find its way into our product backlog.</p> <p>All our services" \
        " are currently free of charge - so you can go wild! Try it now <a href=\"https://app.daita.tech\"style=\"text-decoration:none;color:inherit;border-bottom: solid 2px\">here</a>.</p> <p>Cheers,</p> <p>The DAITA Team</p>".format(
            mail)
    return generate_response(
        message=MessageGetTemapleMailSuccessFully,
        data={"content": template},
        headers=RESPONSE_HEADER
    )
