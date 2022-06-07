import json
from http import HTTPStatus
from typing import *
import traceback


RESPONSE_HEADER = {
    "access-control-allow-origin": "*",
    "access-control-allow-headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent",
}

# RESPONSE_HEADER_2 = {
#     'Access-Control-Allow-Headers': 'Content-Type',
#     'Access-Control-Allow-Origin': '*',
#     'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
# }


def generate_response(
    message: str,
    status_code: int = HTTPStatus.OK,
    headers: dict = {},
    data: dict = {},
    cookie: str = "",
    error: bool = False,
    is_in_stepfunction: bool = False,
    is_use_header_2: bool = False,
):

    # if is_use_header_2:
    #     headers = RESPONSE_HEADER_2
    # else:
    headers.update(RESPONSE_HEADER)

    body = {"message": message, "data": data, "error": error}

    if is_in_stepfunction:
        return {
            "statusCode": status_code,
            "body": body,
        }
    else:
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
            print(repr(exc))
            print(traceback.format_exc())
            messageRaw = str(repr(exc))

            return generate_response(
                message=messageRaw.replace("Exception('", "")
                .replace("')", "")
                .replace('Exception("', "")
                .replace('")', ""),
                error=True,
            )

    return exception_handler
