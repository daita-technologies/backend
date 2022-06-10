import json
import base64

import boto3


client = boto3.client("ses")


def get_email(id_token):
    header, payload, signature = id_token.split(".")
    user_info = json.loads(base64.b64decode(payload + "=" * 10))  # add missing padding
    return user_info["email"]


def lambda_handler(event, context):
    email = get_email(event["id_token"])
    print("send mail")
    message = """
        <p>Dear User,</p>
        <p>Your download link has been created. Please log into DAITA Platform and go to <a href='https://app.daita.tech/task-list'>My Tasks</a> to download your files.</p>
        <p>Best,</p>
        <p>The DAITA Team</p>
        <p>---</p>
        <p><i>In case you encounter any issues or questions, please contact us at <a href = "mailto: contact@daita.tech">contact@daita.tech</a>.</i></p>
        """
    message_email_text = """
        Dear User,
        Your download link has been created. Please log into DAITA Platform and go to https://app.daita.tech/task-list to download your files.
        Best,
        The DAITA Team
        ---
        In case you encounter any issues or questions, please contact us at contact@daita.tech.
        """
    response = client.send_email(
        Destination={
            "ToAddresses": [email],
        },
        Message={
            "Subject": {
                "Charset": "UTF-8",
                "Data": "Your files are ready for download",
            },
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": message,
                },
                "Text": {
                    "Charset": "UTF-8",
                    "Data": message_email_text,
                },
            },
        },
        Source="DAITA Team <noreply@daita.tech>",
    )
    return {
        "error": False,
        "success": True,
        "message": "Email sent! Message ID: {}".format(response["MessageId"]),
        "data": None,
    }
