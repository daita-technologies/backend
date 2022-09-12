import os
import json
import logging
from datetime import datetime
from http import HTTPStatus

import boto3

from config import *
from error_messages import *
from response import generate_response, error_response
from lambda_base_class import LambdaBaseClass
from utils import *


logger = logging.getLogger(__name__)
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
ACCESS_TOKEN_EXPIRATION = 24 * 60 * 60
RESPONSE_HEADER = {
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
##################################################################################################################
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


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


@error_response
def lambda_handler(event, context):
    return RefreshTokenClass().handle(event, context)


class RefreshTokenClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.username = body["username"]
        self.refresh_token = body["refresh_token"]

    def handle(self, event, context):
        self.parser(event)
        try:
            authenticated = cog_provider_client.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": self.refresh_token,
                    "USERNAME": self.username,
                },
                ClientId=CLIENTPOOLID,
            )

            id_token = authenticated["AuthenticationResult"]["IdToken"]
            IdentityId = aws_get_identity_id(
                id_token, USERPOOLID, IDENTITY_POOL)

            # call Cognito getCredentialsForIdentity
            identity = cog_identity_client.get_credentials_for_identity(
                IdentityId=IdentityId,
                Logins={
                    f'cognito-idp.{cog_identity_client.meta.region_name}.amazonaws.com/{USERPOOLID}': id_token
                }
            )
        except Exception as exc:
            print(exc)
            raise Exception(MessageRefreshTokenError) from exc
        tempusername = self.username
        tempusername = tempusername.lower()
        if 'github' in tempusername or 'google' in tempusername:
            name = getDisplayName(self.username)
        else:
            name = self.username
        # reformat
        user_data = {
            "access_key": identity["Credentials"]["AccessKeyId"],
            "secret_key": identity["Credentials"]["SecretKey"],
            "session_key": identity["Credentials"]["SessionToken"],
            "token": authenticated["AuthenticationResult"]["AccessToken"],
            "identity_id": identity["IdentityId"],
            # expire time in seconds
            "credential_token_expires_in": (identity["Credentials"]["Expiration"].timestamp())*1000,
            "id_token": id_token,
            "token_expires_in": float(int((datetime.now().timestamp() + ACCESS_TOKEN_EXPIRATION)*1000)),
            "username": self.username,
            "name": name
        }

        # return response
        return generate_response(
            message=MessageRefreshTokenSuccessfully,
            status_code=HTTPStatus.OK,
            headers=RESPONSE_HEADER,
            data=user_data,
        )
