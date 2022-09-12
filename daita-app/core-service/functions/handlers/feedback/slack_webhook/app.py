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
from error_messages import *
from response import *
from config import *
import tempfile
from models.feedback_model import *
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']
REGION = os.environ['REGION']
OAUTH2BOT = 'xoxb-2966360820768-3760970933602-MoApe9duMpoO5KAa6HaCUzzY' # not dev env 
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
############################################################################################################
s3 = boto3.client('s3')


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





@error_response
def lambda_handler(event, context):
    headers = event['headers']['Authorization']
    authorization_header = headers
    token = authorization_header.replace('Bearer ', '')
    feedbackDB = Feedback()

    if not len(authorization_header):
        raise Exception(MessageMissingAuthorizationHeader)

    try:
        body = json.loads(event['body'])
        text = body['text']
        images = body['images']
    except Exception as e:
        print(e)
        raise Exception(MessageUnmarshalInputJson)

    if len(text) > 750:
        raise Exception(MessageErrorFeedbackLimitword)
    if not isinstance(images, list):
        raise Exception(MessageErrorFeedbackInvalidType)

    if len(images) > 3:
        raise Exception(MessageErrorFeedbackLimitImages)
    for it in images:
        if not validFileImage(it):
            raise Exception(MessageErrorInvalidExtension)
    try:
        username = claimsToken(token, 'username')
    except Exception as e:
        raise e
    info = {}
    while True:
        key = str(uuid.uuid4())
        UTC = pytz.utc
        datetimeUTC = datetime.now(UTC)
        datetimeString = datetimeUTC.strftime('%Y:%m:%d %H:%M:%S %Z %z')
        if not feedbackDB.CheckKeyIsExist(key):
            info = {
                "ID": key,
                "name": username,
                "content": text,
                "images": images,
                "created_time": datetimeString
            }
            feedbackDB.CreateItem(info)
            break
    message = "Username: {}\n Time: {}\n Content: {}".format(
        getDisplayName(info['name']), info['created_time'], info['content'])
    fileList = []
    dir = tempfile.TemporaryDirectory(dir='/tmp')
    dirname = dir.name
    try:
        for it in images:
            bucket, filename = split(it)
            resultS3 = s3.get_object(Bucket=bucket, Key=filename)
            tmpfile = os.path.join(dirname, os.path.basename(filename))
            fileList.append(tmpfile)
            with open(tmpfile, 'wb') as file:
                file.write(resultS3['Body'].read())
    except Exception as e:
        print(e)
        raise Exception(e)
    print(f'Debug Feedback{message}')
    # postMessageWithFiles(message, fileList, CHANNELWEBHOOK)
    dir.cleanup()
    return generate_response(
        message=MessageSendFeedbackSuccessfully,
        data={},
        headers=RESPONSE_HEADER
    )
