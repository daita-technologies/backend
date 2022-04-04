from http import HTTPStatus

import requests

from config import *


def verify_captcha(token: str):
    payload = {
        "secret": SECRETKEYGOOGLE,
        "sitekey": SITEKEYGOOGLE,
        "response": token
    }

    response = requests.post(
        ENDPOINTCAPTCHAVERIFY,
        params=payload
    )
    print(response.json())
    if not response.json()["success"]:
        raise Exception("Verify captcha failed")
