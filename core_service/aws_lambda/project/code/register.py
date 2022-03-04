from cmath import inf
import os
import json
import logging
from http import HTTPStatus
import os
import boto3
from dataclasses import dataclass
import howard
import re 

from error import *
from response import *
from config import *
from datetime import datetime
def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[\^$*.\[\]{}\(\)?\-\"!@#%&\/,><\':;|_~`])\S{8,99}$"
class User(object):
    def __init__(self):
        self.db_client = boto3.resource('dynamodb',region_name=REGION,aws_access_key_id=ACCESSKEYID,aws_secret_access_key=SECRETACCESS)
    def create_item(self,info):
        self.db_client.Table("User").put_item(Item={
            'ID': info['ID'],
            'username': info['username'],
            'role': 'normal',
            'status':'deactivate',
            'create_at': convert_current_date_to_iso8601()
            })

def checkInvalidUserRegister(user,mail):
    response = cog_provider_client.list_users(
        UserPoolId=USERPOOLID
    )
    info_user =  list(filter(lambda x : x['Username'] == user,response['Users']))
    if len(info_user):
        return False , True
    for index , data in enumerate(response['Users']):
        for  info in data['Attributes']:
            if info['Name'] == 'email' and info['Value'] == mail:
                return True, False
    return True, True

@error_response
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        username = body['username']
        mail = body['mail']
        password = body['password']
    except Exception as e:
        print(e)
    
    if not re.match(PASSWORD_REGEX, password):
        raise Exception(MessageInvalidPassword)
    checkUsername, checkemail = checkInvalidUserRegister(username,mail)
    if not checkUsername:
        raise Exception(MessageSignUpUsernameInvalid)
    elif not checkemail:
        raise Exception(MessageSignUPEmailInvalid)
    try:
        respUserSignUp = cog_provider_client.sign_up(
            ClientId=CLIENTPOOLID,
            Username= username,
        Password= password
        )
    except Exception as e:
        print(e)
        raise Exception(MessageSignUpFailed)
    model = User()
    try :
        model.create_item({
            'ID': respUserSignUp['UserSub'],
            'username': username
        })
    except Exception as e :
        print(e)
        raise Exception(MessageSignUpFailed)
    return generate_response(
            message="Sign up for user {} was successful".format(username),
            data=response,
            headers=RESPONSE_HEADER
        )