from cmath import inf
from getpass import getuser
import os
import json
import re
from datetime import datetime
import os
import boto3
from utils import aws_get_identity_id

from error import *
from response import *
from config import *
from eventID import CreateEventUserLogin, CheckEventUserLogin
from verify_captcha import *

ACCESS_TOKEN_EXPIRATION = 24 * 60 * 60
mailRegexString =re.compile('([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')

RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}

######################################################################################
def getUsernameByEmail(email):
    client = cog_provider_client.list_users(
    UserPoolId=USERPOOLID)
    for _ , data in enumerate(client['Users']):
        for info in data['Attributes']:
            if info['Name'] == 'email' and info['Value'] == email and data['UserStatus'] == "CONFIRMED":
                return data['Username']
    return None

#######################################################################################
def getSub(access_token):
    resp = cog_provider_client.get_user(
        AccessToken=  access_token
    )
    sub = [a['Value'] for a in resp['UserAttributes'] if a['Name'] == 'sub'][0]
    return sub 

#######################################################################################
def checkEmailVerified(access_token):
    resp = cog_provider_client.get_user(
        AccessToken=  access_token
    )

    for it in resp['UserAttributes']:
        if it['Name'] == 'email_verified' and it['Value'] == 'false':
            return False
    return True

####################################################################################
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
#############################################################################################################
def createKMSKey(identity):
    alias_name = identity.split(":")[1]
    kms = boto3.client("kms", region_name=REGION)

    key = kms.create_key()
    key_id = key["KeyMetadata"]["KeyId"]
    kms.create_alias(
        AliasName= "alias/"+alias_name,
        TargetKeyId = key_id
    )
    return key_id
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
#############################################################################################################

@error_response
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        username = body['username']
        password = body['password']
        captcha = body['captcha']
    except Exception as e:
        print("error ",e)
        return generate_response(
            message=MessageUnmarshalInputJson,
            data={},
            headers=RESPONSE_HEADER,
            error = True
        )
    
    try:
        verify_captcha(captcha)
    except Exception as exc:
        print(exc)
        raise Exception(MessageCaptchaFailed) from exc
    
    if re.fullmatch(mailRegexString,username):
        username = getUsernameByEmail(email=username)
        print("[DEBUG] username {}".format(username))
        if username is None:
            raise Exception(MessageLoginMailNotExist)

    try:
        model = User() 
    except Exception as e:
        print(e)
        return generate_response(
            message=MessageUnmarshalInputJson,
            data={},
            headers=RESPONSE_HEADER,
            error = True
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
    except cog_provider_client.exceptions.UserNotConfirmedException :
        return generate_response(
            message=MessageUserVerifyConfirmCode,
            data={},
            headers=RESPONSE_HEADER,
            error = True
        )
    except Exception as e:
        print(e)
        return generate_response(
            message=MessageLoginFailed,
            data={},
            headers=RESPONSE_HEADER,
            error = True
        )

    response = {
        'token': authResponse['AuthenticationResult']['AccessToken'],
        'resfresh_token': authResponse['AuthenticationResult']['RefreshToken'],
        'id_token': authResponse['AuthenticationResult']['IdToken'],
        'token_expires_in': float(int((datetime.now().timestamp() + ACCESS_TOKEN_EXPIRATION)*1000))
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
            headers=RESPONSE_HEADER,
            error = True)
        
    sub = getSub(response['token'])
    
    # # check the user is login another device
    # if CheckEventUserLogin(sub):
    #     raise Exception(MessageAnotherUserIsLoginBefore)
    # else:
    #     CreateEventUserLogin(sub)

    if not model.checkFirstLogin(ID=sub,username=username):
        if 'IS_ENABLE_KMS' in os.environ and eval(os.environ['IS_ENABLE_KMS']) == True:
            kms = createKMSKey(credentialsForIdentity['identity_id'])
        else:
            kms = ''
        model.updateActivateUser(info={
            'indentityID': credentialsForIdentity['identity_id'] ,
            'ID': sub,
            'username': username,
            'kms': kms,
        })
    
    
    for k , v in credentialsForIdentity.items():
        response[k] = v 
    response['username'] = username
    response['name'] = username
    return generate_response(
            message=MessageSignInSuccessfully,
            data=response,
            headers=RESPONSE_HEADER
        )