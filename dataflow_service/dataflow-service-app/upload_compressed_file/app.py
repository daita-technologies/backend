import os
import json

import boto3


sqs = boto3.client('sqs')
queue_url = os.getenv("DECOMPRESS_FILE_QUEUE_URL")

# import requests


def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    # file path in S3
    uploaded_file = event["file"]

    # add a message to decompress file queue
    response = sqs.send_message(
        QueueUrl=queue_url,
        DelaySeconds=10,
        MessageBody=(
            uploaded_file
        )
    )
    print(response['MessageId'])

    print("succeed")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "succeed",
        }),
    }
