import boto3
import os
from config import *
from error_messages import *

def aws_get_identity_id(id_token, USER_POOL_ID=os.environ.get("COGNITO_USER_POOL", ""), IDENTITY_POOL_ID=os.environ.get("IDENTITY_POOL", "")):
    identity_client = boto3.client('cognito-identity')
    PROVIDER = f'cognito-idp.{identity_client.meta.region_name}.amazonaws.com/{USER_POOL_ID}'

    try:
        identity_response = identity_client.get_id(
            IdentityPoolId=IDENTITY_POOL_ID,
            Logins={PROVIDER: id_token})
    except Exception as e:
        print('Error: ', repr(e))
        raise Exception(MESS_AUTHEN_FAILED) from e

    identity_id = identity_response['IdentityId']

    return identity_id