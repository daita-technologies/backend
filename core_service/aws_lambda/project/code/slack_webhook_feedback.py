import requests
import json
import pytz
import os
import json
from datetime import datetime
from http import HTTPStatus
import os
import uuid
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
############################################################################################################
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
    elif "given_name" in user_attributes or \
        "family_name" in user_attributes:
        name = f"{user_attributes.pop('given_name', '')} {user_attributes.pop('family_name', '')}"
    else:
        name = user_attributes["email"]

    return name
####################################################################################################
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

class Feedback(object):
    def __init__(self):
        self.db_client = boto3.resource('dynamodb',region_name=REGION)
        self.TBL = "feedback"
    def CreateItem(self,info):
         self.db_client.Table(self.TBL).put_item(Item={
             "ID":info["ID"],
             "name":info["name"],
             "content":info["content"],
             "created_time":info["created_time"],
         })
    
    def CheckKeyIsExist(self,ID):
        response = self.db_client.Table(self.TBL).get_item(Key={
                "ID":ID
        })
        if 'Item' in response:
            return True
        return False

@error_response
def lambda_handler(event, context):
    headers = event['headers']['Authorization']
    authorization_header = headers
    token = authorization_header.replace('Bearer ','')
    feedbackDB = Feedback()

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
    info = {}
    while True:
        key = str(uuid.uuid4())
        UTC = pytz.utc
        datetimeUTC = datetime.now(UTC)
        datetimeString = datetimeUTC.strftime('%Y:%m:%d %H:%M:%S %Z %z')
        if not feedbackDB.CheckKeyIsExist(key):
            info = {
                "ID":key,
                "name":username,
                "content":text,
                "created_time": datetimeString
            }
            feedbackDB.CreateItem(info)
            break
    message = "Username: {}\n Time: {}\n Content: {}".format(info['name'],info['created_time'],info['content'])
    payload ={"channel":CHANNELWEBHOOK,
    "username":getDisplayName(username),
    "text":message,
    "icon_emoji":":ghost:"}

    req  = requests.post(
        WEBHOOK,json=payload
    )


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