import json
import requests

from config import *
from response import error_response


OAUTH_USERINFO_URL = "user"
OAUTH_USER_EMAIL_URL = "user/emails"


@error_response
def lambda_handler(event, context):
    print(event)
    oauth_token = event["headers"].get("authorization").split("Bearer ")[1]
    userinfo_response = requests.get(
        url=f"{GITHUB_API_URL}/{OAUTH_USERINFO_URL}",
        headers={
            "Authorization": f"token {oauth_token}",
            "Accept": "application/json"
        },
        allow_redirects=False
    )

    useremail_response = requests.get(
        url=f"{GITHUB_API_URL}/{OAUTH_USER_EMAIL_URL}",
        headers={
            "Authorization": f"token {oauth_token}",
            "Accept": "application/json"
        },
        allow_redirects=False
    )
    useremails = useremail_response.json()
    for email in useremails:
        if email["primary"]:
            primary_email = email["email"]
            break
    else:
        primary_email = None

    body = userinfo_response.json()
    print(body)
    body["email"] = primary_email
    return json.dumps(
            {
                **body,
                "sub": body["id"]
            }
        )