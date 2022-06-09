import boto3
import json
import random
from boto3 import resource
from boto3.dynamodb.conditions import Key


def invoke_sendmail_cognito_service(subject, destination_email, message_email):
    client = boto3.client("lambda")
    payload_json = None
    try:
        response = client.invoke(
            FunctionName="staging-sendmail-cognito-service",
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {
                    "subject": subject,
                    "destination_email": destination_email,
                    "message_email": message_email,
                }
            ),
        )
        payload_json = json.loads(response["Payload"].read())
    except Exception as e:
        return None, e

    return payload_json, None


class TriggerCustomMailcode:
    def __init__(self, REGION):
        self.db_client = boto3.resource("dynamodb", region_name=REGION)
        self.TBL = "Trigger_send_code"

    def create_item(self, info):
        self.db_client.Table(self.TBL).put_item(
            Item={"user": info["user"], "code": info["code"]}
        )

    def query_all_partition_key(self, value):
        filteringExp = Key("user").eq(value)
        return self.db_client.Table(self.TBL).query(KeyConditionExpression=filteringExp)

    def delete_item(self, info):
        items = (self.query_all_partition_key(value=info["user"])).get("Items")
        # print(items)
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
    modelTrigger = TriggerCustomMailcode(REGION=info["region"])
    modelTrigger.create_item({"user": info["user"], "code": confirmCode})
    invoke_sendmail_cognito_service(
        info["subject"],
        info["mail"],
        """
        <p>Your confirmation code is {}.</p>
        <p>Best,</p>
        <p>The DAITA Team</p>
        <p>---</p>
        <p>In case you encounter any issues or questions, please contact us at <a href = "mailto: contact@daita.tech">contact@daita.tech</a>.</p>
        """.format(
            confirmCode
        ),
    )


def DeleteConfirmCode(info):
    modelTrigger = TriggerCustomMailcode(REGION=info["region"])
    if not modelTrigger.find_item({"user": info["user"], "code": info["code"]}):
        raise Exception(
            "A wrong confirmation code has been entered. If you have requested a new confirmation code, use only the latest code."
        )

    modelTrigger.delete_item({"user": info["user"]})


def AddInsertConfirmCode(info):
    modelTrigger = TriggerCustomMailcode(REGION=info["region"])
    modelTrigger.create_item({"user": info["user"], "code": info["confirm_code"]})


def ResendCodeConfirm(info):
    modelTrigger = TriggerCustomMailcode(REGION=info["region"])

    try:
        modelTrigger.delete_item({"user": info["user"]})
    except Exception as e:
        raise Exception(e)
    confirmCode = str(random.randint(100000, 999999))
    modelTrigger.create_item({"user": info["user"], "code": confirmCode})
    invoke_sendmail_cognito_service(
        info["subject"],
        info["mail"],
        """
        <p>Your confirmation code is {}.</p>
        <p>Best,</p>
        <p>The DAITA Team</p>
        <p>---</p>
        <p>In case you encounter any issues or questions, please contact us at <a href = "mailto: contact@daita.tech">contact@daita.tech</a>.</p>
        """.format(
            confirmCode
        ),
    )
