import os
import boto3
import cognitojwt
from error_messages import *
from response import *
from config import *
from models.event_model import EventUser

cog_provider_client = boto3.client('cognito-idp')
cog_identity_client = boto3.client('cognito-identity')
RESPONSE_HEADER = {
    "Access-Control-Allow-Creentials": "true",
	"Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}
eventModel = EventUser()
def claimsToken(jwt_token,field):
    """
    Validate JWT claims & retrieve user identifier
    """
    token = jwt_token.replace("Bearer ", "")
    print(token)
    try:
        verified_claims = cognitojwt.decode(
            token, os.environ['REGION'], os.environ['COGNITO_USER_POOL']
        )
    except Exception as e:
        print(e)
        raise e

    return verified_claims.get(field)

@error_response
def lambda_handler(event, context):
    headers = event['headers']['authorization']
    authorization_header = headers
    if not len(authorization_header):
        raise Exception(MessageMissingAuthorizationHeader)
    try:
        sub = claimsToken(authorization_header,'sub')
        username = claimsToken(authorization_header,'username')
    except Exception as e:
        raise e
    code = None 
    data = {}
    if 'github' in username or 'google' in username:
         code = eventModel.get_code_oauth2_cognito(sub)
         data['code'] = code

    return generate_response(
            message= MessageLogoutSuccessfully,
            headers=RESPONSE_HEADER,
            data = data
        )