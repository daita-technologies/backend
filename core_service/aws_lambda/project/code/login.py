import os
import json
import logging
from datetime import datetime
from http import HTTPStatus
import os
import boto3
from dataclasses import dataclass
from utils import aws_get_identity_id

from error import *
from response import *
from config import *
ACCESS_TOKEN_EXPIRATION = 24 * 60 * 60

cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
"""

UserName string `json:"username"`
	Password string `json:"password"`
	Captcha  string `json:"captcha"`
"""
class UserLoginModel:
    username : str
    password: str
    # captcha: str

def getSub(access_token):
    resp = cog_provider_client.get_user(
        AccessToken=  access_token
    )
    sub = [a['Value'] for a in resp['UserAttributes'] if a['Name'] == 'sub'][0]
    return sub 

def checkEmailVerified(access_token):
    resp = cog_provider_client.get_user(
        AccessToken=  access_token
    )

    for it in resp['UserAttributes']:
        if it['Name'] == 'email_verified' and it['Value'] == 'false':
            return False
    return True


class User(object):
    def __init__(self):
        self.db_client = boto3.resource('dynamodb',region_name=REGION)
    
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


@error_response
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        username = body['username']
        password = body['password']
    except Exception as e:
        print("error ",e)
        return generate_response(
            message=MessageUnmarshalInputJson,
            data={},
            headers=RESPONSE_HEADER
        )
    try:
        model = User() 
    except Exception as e:
        print(e)
        return generate_response(
            message=MessageUnmarshalInputJson,
            data={},
            headers=RESPONSE_HEADER
        )
    try :
        authResponse = cog_provider_client.initiate_auth(
            ClientId=CLIENTPOOLID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME':  username,
                'PASSWORD': password
            }
        )
    except Exception as e:
        print(e)
        return generate_response(
            message=MessageAuthenFailed,
            data={},
            headers=RESPONSE_HEADER
        )

    response = {
        'token': authResponse['AuthenticationResult']['AccessToken'],
        'resfresh_token': authResponse['AuthenticationResult']['RefreshToken'],
        'id_token': authResponse['AuthenticationResult']['IdToken'],
        'token_expires_in': datetime.now().timestamp() + ACCESS_TOKEN_EXPIRATION
    }
    if not checkEmailVerified(response['token']):
        raise Exception(MessageUserVerifyConfirmCode)
        
    try:
        credentialsForIdentity = getCredentialsForIdentity(authResponse['AuthenticationResult']['IdToken'])
    except Exception as e:
        print(e)
        return generate_response(
            message=MessageAuthenFailed,
            data={},
            headers=RESPONSE_HEADER)
        
    sub = getSub(response['token'])


    if not model.checkFirstLogin(ID=sub,username=username):
        kms = createKMSKey(credentialsForIdentity['identity_id'])
        model.updateActivateUser(info={
            'indentityID': credentialsForIdentity['identity_id'] ,
            'ID': sub,
            'username': username,
            'kms': kms,
        })
    
    for k , v in credentialsForIdentity.items():
        response[k] = v 
    response['username'] = username
    print(response)
    return generate_response(
            message=MessageSignInSuccessfully,
            data=response,
            headers=RESPONSE_HEADER
        )