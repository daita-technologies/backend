import json
import boto3
import hashlib
import hmac
import base64
import os
import uuid
from botocore.exceptions import ClientError


def convert_response(data):
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
        },
        "body": json.dumps(data),
    }


def lambda_handler(event, context):
    try:
        destination_email = event["destination_email"]
        message_email = event["message_email"]
        message_email_text = event["message_email_text"]
        subject = event["subject"]
    except Exception as e:
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    client = boto3.client("ses")
    print("send mail")
    try:
        response = client.send_email(
            Destination={
                "ToAddresses": [destination_email],
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": "UTF-8",
                        "Data": message_email,
                    },
                    "Text": {"Charset": "UTF-8", "Data": message_email_text},
                },
                "Subject": {"Charset": "UTF-8", "Data": subject},
            },
            Source="DAITA Team <noreply@daita.tech>",
        )
    except ClientError as e:
        print(e)
        return convert_response(
            {"error": True, "success": False, "message": e, "data": None}
        )
    print(response["MessageId"])
    return convert_response(
        {
            "error": False,
            "success": True,
            "message": response["MessageId"],
            "data": None,
        }
    )
