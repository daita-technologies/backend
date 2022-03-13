import time
import json

def lambda_handler(event, context):
    print(event)
    
    # create sub task for next progress

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "hello world",
            # "location": ip.text.replace("\n", "")
        }),
    }