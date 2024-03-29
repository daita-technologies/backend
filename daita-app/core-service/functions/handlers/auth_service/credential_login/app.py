from email import header
import os
import json
import logging
import time
from datetime import datetime
from http import HTTPStatus
import os
import boto3
import cognitojwt
from utils import  aws_get_identity_id
from urllib.parse import urlparse, quote
from error_messages import *
from response import *
from config import *
from utils import *
from models.event_model import *
import requests
from urllib.parse import urlencode
from lambda_base_class import LambdaBaseClass

ACCESS_TOKEN_EXPIRATION = 24 * 60 * 60
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']
AUTH_ENDPOINT = os.environ['AUTH_ENDPOINT']
REGION = os.environ['REGION']
STAGE = os.environ['STAGE']
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
# endpoint = 'https://devdaitaloginsocial.auth.us-east-2.amazoncognito.com/oauth2/token'

endpoint = os.environ['OAUTH_ENPOINT']


TableUser = os.environ['TABLE_USER']


def getRedirectURI():
    return f'https://{AUTH_ENDPOINT}.execute-api.{REGION}.amazonaws.com/{STAGE}/auth/login_social'

#############################################################################################################################################################


def getMail(user):
    response = cog_provider_client.list_users(
        UserPoolId=USERPOOLID
    )
    # info_user =  list(filter(lambda x : x['Username'] == user,response['Users']))

    for _, data in enumerate(response['Users']):
        if data['Username'] == user:
            for info in data['Attributes']:
                if info['Name'] == 'email':
                    return info['Value']
    return None


def checkInvalidUserRegister(user, mail):
    isCheckMail = True
    response = cog_provider_client.list_users(
        UserPoolId=USERPOOLID
    )
    for _, data in enumerate(response['Users']):
        for info in data['Attributes']:
            if info['Name'] == 'email' and info['Value'] == mail and data['Username'] != user:
                isCheckMail = False
                # break
    return isCheckMail
#############################################################################################################################################################


def createKMSKey(identity):
    alias_name = identity.split(":")[1]
    kms = boto3.client("kms", region_name=REGION)

    key = kms.create_key()
    key_id = key["KeyMetadata"]["KeyId"]
    kms.create_alias(
        AliasName="alias/"+alias_name,
        TargetKeyId=key_id
    )
    return key_id

#############################################################################################################


def getCredentialsForIdentity(token_id):
    PROVIDER = f'cognito-idp.{REGION}.amazonaws.com/{USERPOOLID}'
    responseIdentity = aws_get_identity_id(
        token_id, USERPOOLID, IDENTITY_POOL)
    credentialsResponse = cog_identity_client.get_credentials_for_identity(
        IdentityId=responseIdentity,
        Logins={
            PROVIDER: token_id
        })
    return {
        'secret_key': credentialsResponse['Credentials']['SecretKey'],
        'session_key': credentialsResponse['Credentials']['SessionToken'],
        'credential_token_expires_in': credentialsResponse['Credentials']['Expiration'].timestamp() * 1000,
        'access_key': credentialsResponse['Credentials']['AccessKeyId'],
        'identity_id': responseIdentity
    }
#############################################################################################################


def Oauth2(code):
    print(f'check {code} {getRedirectURI()}')
    params = {"code": code, "grant_type": "authorization_code", "redirect_uri": getRedirectURI(
    ), 'client_id': CLIENTPOOLID, 'scope': 'email+openid+phone+profile'}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = urlencode(params)
    result = requests.post(endpoint, data=data, headers=headers)
    print(result.text)
    return result
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
    # return None
#######################################################################################################


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
        verified_claims = {}

    return verified_claims.get(field)
#############################################################################################################################################################


class User(object):
    def __init__(self):
        self.db_client = boto3.resource('dynamodb')
        self.TBL = TableUser

    def IsNotcheckFirstLogin(self, ID, username):
        response = self.db_client.Table(self.TBL).get_item(
            Key={
                'ID': ID,
                'username': username
            }
        )
        if 'Item' in response and (response['Item']['status'] == "activate" or response['Item']['status'] == "deactivate"):
            return True
        return False

    def updateActivateUser(self, info):
        self.db_client.Table(self.TBL).update_item(
            Key={'ID': info['ID'], 'username': info['username']},
            UpdateExpression="SET  #s = :s , #i = :i , #k = :k , #u = :u",
            ExpressionAttributeValues={
                ':s': 'activate',
                ':i': info['indentityID'],
                ':k': info['kms'],
                ':u': datetime.now().isoformat(),
            },
            ExpressionAttributeNames={
                '#s': 'status',
                '#i': 'identity_id',
                '#k': 'kms_key_id',
                '#u': 'update_at'
            }
        )
#############################################################################################################################################################


class CredentialSocialLoginClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.code = body['code']

    def handle(self, event, context):
        self.parser(event)
        model = User()
        resq = Oauth2(self.code)
        if resq.status_code != 200:
            raise Exception("Login Social Failed")
        resqData = resq.json()
        sub, username = claimsToken(resqData['access_token'], 'sub'), claimsToken(
            resqData['access_token'], 'username')
        mail = getMail(username)
        checkemail = checkInvalidUserRegister(user=username, mail=mail)
        if not CheckEventUserLogin(sub):
            CreateEventUserLoginOauth2(sub, self.code)
        try:
            credentialsForIdentity = getCredentialsForIdentity(
                resqData['id_token'])
        except Exception as e:
            print(e)
            return generate_response(
                message=MessageAuthenFailed,
                data={},
                headers=RESPONSE_HEADER)
        if not model.IsNotcheckFirstLogin(ID=sub, username=username):
            if not checkemail:
                resp = cog_provider_client.admin_delete_user(
                    UserPoolId=USERPOOLID,
                    Username=username
                )
                print(resp)
                raise Exception(MessageSignUPEmailInvalid)
            responseIdentity = aws_get_identity_id(
                resqData['id_token'], USERPOOLID, IDENTITY_POOL)
            if 'IS_ENABLE_KMS' in os.environ and eval(os.environ['IS_ENABLE_KMS']) == True:
                kms = createKMSKey(responseIdentity)
            else:
                kms = ''
            model.updateActivateUser(info={
                'indentityID': responseIdentity,
                'ID': sub,
                'username': username,
                'kms': kms,
            })
        name = getDisplayName(username)
        result = {
            'token': resqData['access_token'],
            'resfresh_token': resqData['refresh_token'],
            'access_key':  credentialsForIdentity['access_key'],
            'session_key':       credentialsForIdentity['session_key'],
            'id_token':        resqData['id_token'],
            'credential_token_expires_in':    credentialsForIdentity['credential_token_expires_in'],
            'token_expires_in': float(int((datetime.now().timestamp() + ACCESS_TOKEN_EXPIRATION)*1000)),
            'secret_key':                credentialsForIdentity['secret_key'],
            'identity_id': credentialsForIdentity['identity_id'],
            'username': username,
            'name': name
        }
        return generate_response(
            message=MessageSuccessfullyCredential,
            data=result,
            headers=RESPONSE_HEADER
        )


@error_response
def lambda_handler(event, context):
    return CredentialSocialLoginClass().handle(event=event, context=context)
