import json
import os
import boto3

from config import *
from response import *
from error_messages import *
from identity_check import *
from utils import *
from models.generate_daita_upload_token import GenerateDaitaUploadTokenModel
generate_daita_upload_token_model = GenerateDaitaUploadTokenModel(
    os.environ['T_GEN_DAITA_UPLOAD_TOKEN'])
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']

def lambda_handler(event, context):

    try:
        body = json.loads(event['body'])
        project_id = body['project_id']
        project_name = body['project_name']
        id_token = body["id_token"]
    except Exception as e:
        print(e)
        return generate_response(
            message=str(e),
            status_code=HTTPStatus.OK,
            data={},
            error=True)

    try:
        identity_id =  aws_get_identity_id(id_token, USERPOOLID, IDENTITY_POOL)
    except Exception as e:
        print(e)
        return generate_response(
            message=str(e),
            status_code=HTTPStatus.OK,
            data={},
            error=True)

    token_existed = generate_daita_upload_token_model.token_exsited(
        identity_id=identity_id, project_id=project_id)

    if not token_existed is None:
        token = token_existed['token']
        return generate_response(
            status_code=HTTPStatus.OK,
            message="Generate daita upload token successful!",
            data={
                "token": token
            },
            error=False)

    token = generate_daita_upload_token_model.create_new_token(id_token=id_token,
                                                               identity_id=identity_id, project_id=project_id, project_name=project_name)
    return generate_response(
        status_code=HTTPStatus.OK,
        message="Generate daita upload token successful!",
        data={
            "token": token
        },
        error=False)
