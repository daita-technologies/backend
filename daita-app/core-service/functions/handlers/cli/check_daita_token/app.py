import os
import json
from response import *
from config import *

from models.generate_daita_upload_token import GenerateDaitaUploadTokenModel

generate_daita_upload_token_model = GenerateDaitaUploadTokenModel(
    os.environ['T_GEN_DAITA_UPLOAD_TOKEN'])


def lambda_handler(event, context):
    param = event['queryStringParameters']
    try:
        daita_token = param['daita_token']
    except Exception as e:
        print(e)
        return generate_response(
            message=str(e),
            data={},
            headers=RESPONSE_HEADER,
            error=True)
    info = generate_daita_upload_token_model.query_by_token(token=daita_token)
    if info is None:
        return generate_response(
            message="Token is expired, please get another token!",
            data={},
            headers=RESPONSE_HEADER,
            error=True)
    return generate_response(
        message="OK",
        data={},
        headers=RESPONSE_HEADER,
        error=False)
