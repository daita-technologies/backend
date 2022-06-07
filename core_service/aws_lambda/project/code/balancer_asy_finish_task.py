import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr

from utils import convert_response
from balancer_utils import get_ec2_id_link_user, get_ec2_id_default


def lambda_handler(event, context):

    # try to parse request body and check body fields
    try:
        print(event)
        ec2_id = event["ec2_id"]
        task_id = event["task_id"]

    except Exception as e:
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    try:
        db_resource = boto3.resource("dynamodb")
        table = db_resource.Table(os.environ["T_EC2_TASK"])

        table.delete_item(
            Key={
                "ec2_id": ec2_id,
                "task_id": task_id,
            }
        )

    except Exception as e:
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    return convert_response(
        {"data": None, "error": False, "success": True, "message": None}
    )
