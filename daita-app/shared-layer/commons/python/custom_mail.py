import boto3
import json
import random
import time
from boto3 import resource
from boto3.dynamodb.conditions import Key


def invoke_sendmail_cognito_service(lambda_name, subject, destination_email, message_email, message_email_text):
    client = boto3.client("lambda")
    payload_json = None
    try:
        response = client.invoke(
            FunctionName=lambda_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {
                    "subject": subject,
                    "destination_email": destination_email,
                    "message_email": message_email,
                    "message_email_text": message_email_text
                }
            ),
        )
        payload_json = json.loads(response["Payload"].read())
    except Exception as e:
        return None, e

    return payload_json, None


class TriggerCustomMailcode:
    def __init__(self, REGION, Table):
        self.db_client = boto3.resource("dynamodb", region_name=REGION)
        self.TBL = Table

    def create_item(self, info):
        self.db_client.Table(self.TBL).put_item(
            Item={"user": info["user"], "code": info["code"],
                  "time_to_live": 90*60 + 5 + int(time.time())}
        )

    def query_all_partition_key(self, value):
        filteringExp = Key("user").eq(value)
        return self.db_client.Table(self.TBL).query(KeyConditionExpression=filteringExp)

    def delete_item(self, info):
        items = (self.query_all_partition_key(value=info["user"])).get("Items")
        for item in items:
            self.db_client.Table(self.TBL).delete_item(
                Key={"user": item["user"], "code": item["code"]}
            )

    def find_item(self, info):
        response = self.db_client.Table(self.TBL).get_item(
            Key={"user": info["user"], "code": info["code"]}
        )
        return True if "Item" in response else False


def AddTriggerCustomMail(info):
    confirmCode = str(random.randint(100000, 999999))
    modelTrigger = TriggerCustomMailcode(
        REGION=info["region"], Table=info['confirm_code_Table'])
    modelTrigger.create_item({"user": info["user"], "code": confirmCode})
    invoke_sendmail_cognito_service(
        lambda_name=info['lambda_name'],
        subject=info["subject"],
        destination_email=info["mail"],
        message_email="""
        <p>Your confirmation code is {}.</p>
        <p>Best,</p>
        <p>The DAITA Team</p>
        <p>---</p>
        <p><i>In case you encounter any issues or questions, please contact us at <a href = "mailto: contact@daita.tech">contact@daita.tech</a>.</i></p>
        """.format(
            confirmCode
        ),
        message_email_text="""
        Your confirmation code is {}.
        Best,
        The DAITA Team
        ---
        In case you encounter any issues or questions, please contact us at contact@daita.tech.
        """.format(
            confirmCode
        )
    )


def DeleteConfirmCode(info):
    modelTrigger = TriggerCustomMailcode(
        REGION=info["region"], Table=info['confirm_code_Table'])
    if not modelTrigger.find_item({"user": info["user"], "code": info["code"]}):
        raise Exception(
            "A wrong confirmation code has been entered. If you have requested a new confirmation code, use only the latest code."
        )

    modelTrigger.delete_item({"user": info["user"]})


def AddInsertConfirmCode(info):
    modelTrigger = TriggerCustomMailcode(
        REGION=info["region"], Table=info['confirm_code_Table'])
    modelTrigger.create_item(
        {"user": info["user"], "code": info["confirm_code"]})


def ResendCodeConfirm(info):
    modelTrigger = TriggerCustomMailcode(
        REGION=info["region"], Table=info['confirm_code_Table'])

    try:
        modelTrigger.delete_item({"user": info["user"]})
    except Exception as e:
        raise Exception(e)
    confirmCode = str(random.randint(100000, 999999))
    modelTrigger.create_item({"user": info["user"], "code": confirmCode})
    invoke_sendmail_cognito_service(
        lambda_name=info['lambda_name'],
        subject=info["subject"],
        destination_email=info["mail"],
        message_email="""
        <p>Your confirmation code is {}.</p>
        <p>Best,</p>
        <p>The DAITA Team</p>
        <p>---</p>
        <p><i>In case you encounter any issues or questions, please contact us at <a href = "mailto: contact@daita.tech">contact@daita.tech</a>.</i></p>
        """.format(
            confirmCode
        ),
        message_email_text="""
        Your confirmation code is {}.
        Best,
        The DAITA Team
        ---
        In case you encounter any issues or questions, please contact us at contact@daita.tech.
        """.format(
            confirmCode
        )
    )
