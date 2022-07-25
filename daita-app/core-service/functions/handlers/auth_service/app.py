import os
import json
import boto3
from response import *


def lambda_handler(event, context):
    print(event)
    return generate_response(
        message='AUth Service',
        data={},
        headers=RESPONSE_HEADER,
        error=False
    )
