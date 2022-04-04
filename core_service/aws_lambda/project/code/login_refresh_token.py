import os
import json
import logging
from datetime import datetime
from http import HTTPStatus

import boto3

from config import *
from error import *
from response import generate_response, error_response
from utils import create_secret_hash, aws_get_identity_id


logger = logging.getLogger(__name__)
cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
ACCESS_TOKEN_EXPIRATION = 24 * 60 * 60
RESPONSE_HEADER = {
    "Access-Control-Allow-Credentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


@error_response
def lambda_handler(event, context):
    '''
    https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-concepts.html#gettingstarted-concepts-event
    https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    '''
    # get params REFRESH_TOKEN passed by FE in event body
    try:
        username = event["username"]
        refresh_token = event["refresh_token"]
    except Exception as exc:
        raise Exception(MessageUnmarshalInputJson) from exc

    try:
        # init Cognito InitiateAuth
        authenticated = cog_provider_client.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": refresh_token,
                    "SECRET_HASH": create_secret_hash(
                        clientSecret="",
                        username=username,
                        clientPoolID=CLIENTPOOLID
                    )
                },
                ClientId=CLIENTPOOLID,
            )

        id_token = authenticated["AuthenticationResult"]["IdToken"]
        IdentityId = aws_get_identity_id(id_token)

        # call Cognito getCredentialsForIdentity
        identity = cog_identity_client.get_credentials_for_identity(
                IdentityId=IdentityId,
                Logins={
                   f'cognito-idp.{cog_identity_client.meta.region_name}.amazonaws.com/{os.environ["USER_POOL_ID"]}': id_token
                }
            )
    except Exception as exc:
        raise Exception(MessageRefreshTokenError) from exc

    # reformat
    user_data = {
        "access_key": identity["Credentials"]["AccessKeyId"],
        "secret_key": identity["Credentials"]["SecretKey"],
        "session_key": identity["Credentials"]["SessionToken"],
        "token": authenticated["AuthenticationResult"]["AccessToken"],
        "identity_id": identity["IdentityId"],
        "credential_token_expires_in": (identity["Credentials"]["Expiration"].timestamp())*1000, # expire time in seconds
        "id_token": id_token,
        "token_expires_in":float(int((datetime.now().timestamp() + ACCESS_TOKEN_EXPIRATION)*1000)),
        "username": username
    }

    # return response
    return generate_response(
        message=MessageRefreshTokenSuccessfully,
        status_code=HTTPStatus.OK,
        headers=RESPONSE_HEADER,
        data=user_data,
    )
