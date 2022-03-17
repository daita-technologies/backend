from email import header
import os
import json
import logging
from datetime import datetime
from http import HTTPStatus
import os
import boto3
import cognitojwt
from utils import create_secret_hash, aws_get_identity_id

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
        verified_claims = {}

    return verified_claims.get(field)

class User(object):
    def __init__(self):
        self.db_client = boto3.resource('dynamodb')
    
    def checkFirstLogin(self,ID,username):
        response = self.db_client.Table("User").get_item(
              Key={
                   'ID':ID,
                   'username': username
              }
        )
        if 'Item' in response and response['Item']['status'] == "activate":
            return True

        return False
    
    def updateActivateUser(self,info):
        self.db_client.Table("User").update_item(
                    Key={'ID': info['ID'],'username':info['username']},
                    UpdateExpression="SET  #s = :s , #i = :i , #k = :k , #u = :u",
                    ExpressionAttributeValues={
                        ':s':'activate',
                        ':i':info['indentityID'],
                        ':k':info['kms'],
                        ':u': datetime.now().isoformat(),
                    },
                    ExpressionAttributeNames={
                        '#s':'status',
                        '#i':'identity_id',
                        '#k':'kms_key_id',
                        '#u':'update_at'
                    }
                )

def createKMSKey(identity):
    alias_name = identity.split(":")[1]
    kms = boto3.client("kms", region_name="us-west-2")

    key = kms.create_key()
    key_id = key["KeyMetadata"]["KeyId"]
    kms.create_alias(
        AliasName= "alias/"+alias_name,
        TargetKeyId = key_id
    )
    return key_id

def GetTokenCognito(username,refreshToken):
    authenticated = cog_provider_client.admin_initiate_auth(
        AuthFlow='REFRESH_TOKEN_AUTH',
        AuthParameters={
                    "REFRESH_TOKEN": refreshToken,  
                },
                ClientId=CLIENTPOOLID,
                UserPoolId=USERPOOLID
    )
    return authenticated

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
        'session_key': credentialsResponse['Credentials']['SecretKey'],
        'credential_token_expires_in':credentialsResponse['Credentials']['Expiration'].timestamp() * 1000,
        'access_key': credentialsResponse['Credentials']['AccessKeyId'],
        'identity_id':responseIdentity
    }
def Oauth2(code):
    params = {"code": code, "grant_type": "authorization_code", "redirect_uri": getRedirectURI(),'client_id':client_id,'scope':'email+openid+phone+profile'}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = urlencode(params)
    result = requests.post(endpoint, data=data, headers=headers)
    return result
@error_response
def lambda_handler(event, context):
    print(event,type(event))
    param = event['queryStringParameters']
    try:
        code = param['code']
    except Exception as e:
        print(e)
        raise Exception(e)
    model = User()
    resq = Oauth2(code)
    if resq.status_code != 200:
        raise Exception("Login Social Failed")
    resqData = resq.json()
    token = resqData['access_token']
    sub, username = claimsToken(resqData['access_token'],'sub') , claimsToken(resqData['access_token'],'username')

    authenticated = GetTokenCognito(username,resqData['refresh_token'])
    try:
        credentialsForIdentity = getCredentialsForIdentity(authenticated['AuthenticationResult']['IdToken'])
    except Exception as e:
        print(e)
        return generate_response(
                message=MessageAuthenFailed,
                data={},
                headers=RESPONSE_HEADER)
    if not model.checkFirstLogin(ID=sub,username=username):
        kms = createKMSKey(credentialsForIdentity['identity_id'])
        model.updateActivateUser(info={
            'indentityID': credentialsForIdentity['identity_id'] ,
            'ID': sub,
            'username': username,
            'kms': kms,
        })
    path = None
    if 'state' in param:
        path = base64.decode(['state'])
    else: 
        path = 'http://localhost:3000/login'

    location= "{}?token={}&resfresh_token={}&access_key={}&session_key={}&id_token={}&credential_token_expires_in={}&token_expires_in={}&secret_key={}&identity_id={}" \
        .format(path,
        authenticated['AuthenticationResult']['AccessToken'],
        resqData['refresh_token'],
        credentialsForIdentity['access_key'],
        credentialsForIdentity['session_key'],
        authenticated['AuthenticationResult']['IdToken'],
                credentialsForIdentity['credential_token_expires_in']
                ,datetime.now().timestamp() + ACCESS_TOKEN_EXPIRATION,
                credentialsForIdentity['session_key'],
                credentialsForIdentity['identity_id'],username)
    headers = {"Location":location,	"Access-Control-Allow-Methods": "GET,HEAD,OPTIONS,POST,PUT"}
    return {
        "statusCode": 302,
        "headers": headers,
        "body":"",
        "isBase64Encoded": False
    }