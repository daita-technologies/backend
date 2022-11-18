from http import HTTPStatus

import requests

from config import *


def verify_captcha(token: str, site_key_google, secret_key_google):
    payload = {
        "secret": secret_key_google,
        "sitekey": site_key_google,
        "response": token
    }

    response = requests.post(
        ENDPOINTCAPTCHAVERIFY,
        params=payload
    )
    print(response.json())
    if not response.json()["success"]:
        raise Exception("Verify captcha failed")
