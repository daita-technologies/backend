import time
import json
from config import *
from response import *
from images import ImageLoader

def lambda_handler(event, context):
    body =  json.load(event['detail'])
    imageloader = ImageLoader()

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
        }),
    }