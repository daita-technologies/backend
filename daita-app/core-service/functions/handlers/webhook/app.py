import requests
import re
import json
import pytz
import os
import json
from datetime import datetime
from http import HTTPStatus
import os
import uuid
import slack_sdk
import boto3
import cognitojwt
from error import *
from response import *
from config import *
import tempfile

cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
############################################################################################################
s3 = boto3.client('s3')
USERPOOLID = os.environ['COGNITO_CLIENT_ID']


def validFileImage(filename):
    return (os.path.splitext(filename)[1]).lower() in ['.jpeg', '.png', '.jpg']


def split(uri):
    if not 's3' in uri[:2]:
        temp = uri.split('/')
        bucket = temp[0]
        filename = '/'.join([temp[i] for i in range(1, len(temp))])
    else:
        match = re.match(r's3:\/\/(.+?)\/(.+)', uri)
        bucket = match.group(1)
        filename = match.group(2)
    return bucket, filename


def postMessageWithFiles(message, fileList, channel):
    SLACK_TOKEN = OAUTH2BOT
    client = slack_sdk.WebClient(token=SLACK_TOKEN)
    for file in fileList:
        upload = client.files_upload(file=file, filename=file)
        message = message+"<"+upload['file']['permalink']+"| >"
    outP = client.chat_postMessage(
        channel=channel,
        text=message
    )
    print(outP)


def getDisplayName(username):
    response = cog_provider_client.admin_get_user(
        UserPoolId=USERPOOLID,
        Username=username
    )
    user_attributes = {}
    for att in response["UserAttributes"]:
        user_attributes[att["Name"]] = att["Value"]

    name = ""
    if "name" in user_attributes:
        name = user_attributes["name"]
    elif "given_name" in user_attributes or "family_name" in user_attributes:
        name = f"{user_attributes.pop('given_name', '')} {user_attributes.pop('family_name', '')}"
    else:
        name = user_attributes["email"]

    return name
####################################################################################################


def claimsToken(jwt_token, field):
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


class Feedback(object):
    def __init__(self):
        self.db_client = boto3.resource('dynamodb', region_name=REGION)
        self.TBL = os.environ['T_FEEDBACK']

    def CreateItem(self, info):
        self.db_client.Table(self.TBL).put_item(Item={
            "ID": info["ID"],
            "name": info["name"],
            "content": info["content"],
            "images": info["images"],
            "created_time": info["created_time"],
        })

    def CheckKeyIsExist(self, ID):
        response = self.db_client.Table(self.TBL).get_item(Key={
            "ID": ID
        })
        if 'Item' in response:
            return True
        return False
