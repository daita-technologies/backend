import json


def lambda_handler(event, context):
    print(event)
    body = json.loads(event["body"])

    if body["error"]:
        raise Exception("previous step failed")

    print("succeed")
    return {
        "status": "succeed",
    }
