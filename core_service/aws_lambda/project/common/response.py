import html
import json
from http import HTTPStatus
from typing import *


RESPONSE_HEADER = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Origin, Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
}

RESPONSE_HEADER_1 = {
    "Access-Control-Allow-Headers": "Origin, Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS, POST, PUT",
}


def generate_response(
    message: str,
    status_code: int = HTTPStatus.OK,
    headers: dict = {},
    data: dict = {},
    cookie: str = "",
    error: bool = False,
):

    headers.update(RESPONSE_HEADER_1)

    body = {"message": message, "data": data, "error": error}

    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body),
        "isBase64Encoded": False,
    }


def error_response(lambda_handler):
    def exception_handler(*args, **kwargs):
        try:
            return lambda_handler(*args, **kwargs)
        except Exception as exc:
            return generate_response(message=str(exc), error=True)

    return exception_handler
