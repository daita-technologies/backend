from tkinter import E
from lambda_base_class import LambdaBaseClass
import json
import boto3
import hashlib
import hmac
import base64
import os
import uuid
import requests
import random
from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, convert_current_date_to_iso8601, aws_get_identity_id
import const

USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


class ProjectDownloadCreateCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_id = body['project_id']
        self.project_name = body['project_name']
        self.down_type = body['down_type']

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        try:
            identity_id = aws_get_identity_id(
                self.id_token, USERPOOLID, IDENTITY_POOL)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        db_resource = boto3.resource('dynamodb')

        # create task id and save to DB
        try:
            table = db_resource.Table(os.environ["T_TASK_DOWNLOAD"])
            task_id = uuid.uuid4().hex
            task_id = f"{convert_current_date_to_iso8601()}-{task_id}"
            create_time = convert_current_date_to_iso8601()
            table.put_item(
                Item={
                    "identity_id": identity_id,
                    "task_id": task_id,
                    "status": "RUNNING",
                    "process_type": "DOWNLOAD",
                    "project_id": self.project_id,
                    "created_time": create_time,
                }
            )
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        # send request to url
        try:
            url = 'http://'+os.environ["DOWNLOAD_SERVICE_URL"]+':8000/download'
            request_body = {
                "project_id": self.project_id,
                "project_name": self.project_name,
                "down_type": self.down_type,
                "task_id": task_id,
                "identity_id": identity_id
            }
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                url,
                json=request_body,
                headers=headers,
            )

            if response.status_code == 500:
                # error when download
                raise Exception(
                    "There are some error when downloading, please try again")

            value = response.json()
            print('response request: ', value)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        return convert_response(
            {
                'data': {
                    "task_id": task_id
                },
                "error": False,
                "success": True,
                "message": None
            })


def lambda_handler(event, context):
    return ProjectDownloadCreateCls().handle(event=event, context=context)
