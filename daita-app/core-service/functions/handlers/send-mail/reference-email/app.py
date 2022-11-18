import json
import boto3
import os
from botocore.exceptions import ClientError

from utils import convert_response
from config import *

USERPOOLID = os.environ['COGNITO_USER_POOL']


def get_email(user):
    client = boto3.client("cognito-idp")
    try:
        resp = client.list_users(
            UserPoolId=USERPOOLID,
        )
    except Exception as e:
        print(e)
        return None, e
    info_user = list(filter(lambda x: x["Username"] == user, resp["Users"]))
    if len(info_user):
        email = list(
            filter(lambda x: x["Name"] == "email", info_user[0]["Attributes"]))
        return email[0]["Value"], None
    return None, None


def lambda_handler(event, context):
    body = json.loads(event["body"])
    try:
        source_user = body["username"]
        destination_email = body["destination_email"]
    except Exception as e:
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )
    email_name, error = get_email(source_user)
    if error != None:
        return convert_response(
            {"error": True, "success": False,
                "message": str(error), "data": None}
        )
    if email_name == None:
        return convert_response(
            {
                "error": True,
                "success": False,
                "message": "The user is not exist",
                "data": None,
            }
        )
    client = boto3.client("ses")
    print("send mail")
    message_email = """
        <p>Hi,</p>
        <p>{} has invited you to explore DAITA's recently launched <a href='https://app.daita.tech'>data augmentation platform</a>.</p>
        <p>Building a platform that machine learning engineers and data scientists really love is truly hard. But that's our ultimate ambition!</p>
        <p>Thus, your feedback is greatly appreciated, as this first version will still be buggy and missing many features. Please send all your thoughts, concerns, feature requests, etc. to <a href=\"mailto:contact@daita.tech?subject=DAITA%20Platform%20User%20Feedback\"\>contact@daita.tech</a> or simply reply to this e-mail. Please be assured that all your feedback will find its way into our product backlog.</p>
        <p>All our services are currently free of charge - so you can go wild! Try it now <a href='https://app.daita.tech'>here</a>.</p>
        <p>Cheers,</p>
        <p>The DAITA Team</p>
        """.format(
        email_name
    )
    message_email_text = """
        Hi,
        {} has invited you to explore DAITA's recently launched data augmentation platform https://app.daita.tech.
        Building a platform that machine learning engineers and data scientists really love is truly hard. But that's our ultimate ambition!
        Thus, your feedback is greatly appreciated, as this first version will still be buggy and missing many features. Please send all your thoughts, concerns, feature requests, etc. to contact@daita.tech or simply reply to this e-mail. Please be assured that all your feedback will find its way into our product backlog.
        All our services are currently free of charge - so you can go wild! Try it now here https://app.daita.tech.
        Cheers,
        The DAITA Team
        """.format(
        email_name
    )
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
                    "Text": {
                        "Charset": "UTF-8",
                        "Data": message_email_text,
                    },
                },
                "Subject": {
                    "Charset": "UTF-8",
                    "Data": "You've been invited to try DAITA's data augmentation platform for free!",
                },
            },
            Source="DAITA Team <hello@daita.tech>",
        )
    except ClientError as e:
        print(e)
        return convert_response(
            {"error": True, "success": False, "message": e, "data": None}
        )
    return convert_response(
        {
            "error": False,
            "success": True,
            "message": "Email sent! Message ID: {}".format(response["MessageId"]),
            "data": None,
        }
    )
