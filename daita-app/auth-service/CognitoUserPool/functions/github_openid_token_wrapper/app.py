import json
import requests

from config import *
from response import error_response


OAUTH_TOKEN_URL = "login/oauth/access_token"


@error_response
def lambda_handler(event, context):
    response = requests.post(
        url=f"{GITHUB_LOGIN_URL}/{OAUTH_TOKEN_URL}",
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        },
        data=event["body"],
    )
    return {
        "body": json.dumps(response.json()),
        "isBase64Encoded": False
    }
