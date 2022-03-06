from http import HTTPStatus

import requests

from config import *


def verify_captcha(token: str):
    response = requests.post(ENDPOINTCAPTCHAVERIFY)
    payload = {
        "secret": SECRETKEYGOOGLE,
        "sitekey": SITEKEYGOOGLE,
        "response": token
    }

    response = requests.get(
        ENDPOINTCAPTCHAVERIFY,
        params=payload
    )

    if not response.json()["success"]:
        raise Exception("Verify captcha failed")

    return True
