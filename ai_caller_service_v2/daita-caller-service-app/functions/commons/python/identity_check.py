import boto3
import os
from config import *
from error_messages import *

def aws_get_identity_id(id_token):
    identity_client = boto3.client('cognito-identity')
    PROVIDER = f'cognito-idp.{identity_client.meta.region_name}.amazonaws.com/{IDENTITYPOOLID}'

    try:
        identity_response = identity_client.get_id(
                              IdentityPoolId=IDENTITYPOOLID,
                              Logins = {PROVIDER: id_token})
    except Exception as e:
        raise 

    identity_id = identity_response['IdentityId']

    return identity_id