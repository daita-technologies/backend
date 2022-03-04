import html
import json
from http import HTTPStatus
from typing import *


RESPONSE_HEADER = {
    "access-control-allow-origin": "*",
	"access-control-allow-headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
}


def generate_response(
    message: str,
    status_code: int = HTTPStatus.OK,
    headers: dict = {},
    data: dict = {},
    cookie: str = "",
    error: bool = False
    ):

    headers.update(RESPONSE_HEADER)

    body = {
        "message": message,
        "data": data,
        "error": error
    }

    return {
        "statusCode": status_code,
        "headers": headers,
        "body": html.escape(json.dumps(body)),
        "isBase64Encoded": False
    }


def error_response(lambda_handler):
    def exception_handler(*args, **kwargs):
        try:
            return lambda_handler(*args, **kwargs)
        except Exception as exc:
            return(
                generate_response(
                    message=repr(exc),
                    error=True
                )
            )
    return exception_handler

