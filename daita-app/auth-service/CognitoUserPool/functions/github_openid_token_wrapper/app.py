import json
import requests

from config import *
from response import error_response
import base64

OAUTH_TOKEN_URL = "login/oauth/access_token"


@error_response
def lambda_handler(event, context):
    print(event)
    if event["isBase64Encoded"]:
        event["body"] = base64.b64decode(event["body"]).decode("ascii")
    response = requests.post(
        url=f"{GITHUB_LOGIN_URL}/{OAUTH_TOKEN_URL}",
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json'
        },
        data=event["body"],
    )
    print(response.json())
    # return {
    #     "body": json.dumps(response.json()),
    #     "isBase64Encoded": False
    # }
    return json.dumps(response.json())