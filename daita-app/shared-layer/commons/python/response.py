import json
from http import HTTPStatus
from typing import *
import traceback


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
        "body": json.dumps(body),
        "isBase64Encoded": False
    }

def error_response(lambda_handler):
    def exception_handler(*args, **kwargs):
        try:
            return lambda_handler(*args, **kwargs)
        except Exception as exc:
            print(repr(exc))
            print(traceback.format_exc())
            messageRaw = str(repr(exc))            

            return(
                generate_response(
                    message= messageRaw.replace("Exception('", "").replace("')", "").replace("Exception(\"", "").replace("\")", ""),
                    error=True
                )
            )
            
    return exception_handler

