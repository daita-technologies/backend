import json
import requests

from config import *
from response import error_response


OAUTH_USERINFO_URL = "user"


@error_response
def lambda_handler(event, context):
    oauth_token = event["headers"].get("Authorization").split("Bearer ")[1]
    response = requests.get(
        url=f"{GITHUB_API_URL}/{OAUTH_USERINFO_URL}",
        headers={
            "Authorization": f"token {oauth_token}",
            "Accept": "application/json"
        },
        allow_redirects=False
    )

    body = response.json()
    return {
        "body": json.dumps(
            {
                **body,
                "sub": body["id"]
                }
            ),
        "isBase64Encoded": False
    }
