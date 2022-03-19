import time
import json

from s3_utils import test

def lambda_handler(event, context):
    print(event)
    
    test()
    # create sub task for next progress

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }