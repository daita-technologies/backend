import json
import boto3
import hashlib
import hmac
import base64
import os
import uuid
import random
from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, convert_current_date_to_iso8601, aws_get_identity_id
import const


def lambda_handler(event, context):
    try:
        print(event["body"])
        body = json.loads(event["body"])
        id_token = body["id_token"]
        task_id = body["task_id"]

    except Exception as e:
        return convert_response(
            {
                "error": True,
                "success": False,
                "message": "Request body format is wrong!",
                "data": None,
            }
        )

    try:
        identity_id = aws_get_identity_id(id_token)
    except Exception as e:
        print("Error: ", repr(e))
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    db_resource = boto3.resource("dynamodb")

    # create task id and save to DB
    try:
        table = db_resource.Table(os.environ["T_TASK_DOWNLOAD"])
        response = table.get_item(
            Key={
                "identity_id": identity_id,
                "task_id": task_id,
            }
        )
        if response.get("Item", None):
            status = response["Item"].get("status")
            s3_key = response["Item"].get("s3_key", None)
            presign_url = response["Item"].get("presign_url", None)
        else:
            raise Exception(f"Task id ({task_id}) is not exist!")

    except Exception as e:
        print("Error: ", repr(e))
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    return convert_response(
        {
            "data": {"status": status, "s3_key": s3_key, "presign_url": presign_url},
            "error": False,
            "success": True,
            "message": None,
        }
    )
