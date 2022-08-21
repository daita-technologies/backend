import json
import boto3
import hashlib
import hmac
import base64
import os
import uuid
from lambda_base_class import LambdaBaseClass
from utils import convert_response, convert_current_date_to_iso8601, aws_get_identity_id, move_data_s3


class AsyncCreateSample(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.s3_prefix = body["s3_prefix"]
        self.project_id = body["project_id"]
        self.project_name = body["project_name"]
        self.identity_id = body["identity_id"]

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        db_client = boto3.client('dynamodb')
        db_resource = boto3.resource('dynamodb')

        # move data in s3
        PREFIX_SAMPLE = "sample/"
        ls_info = move_data_s3(
            PREFIX_SAMPLE, self.s3_prefix, os.environ["BUCKET_NAME"])

        # update to DB
        # create the batch request from input data and summary the information
        ls_item_request = []
        total_size = 0
        count = 0
        for object in ls_info:
            # update summary information
            size_old = 0
            total_size += (object[2]-size_old)
            if size_old <= 0:
                count += 1

            is_ori = True
            type_method = 'ORIGINAL'
            item_request = {
                'project_id': self.project_id,  # partition key
                's3_key': object[1],          # sort_key
                'filename': object[0],
                'hash': '',      # we use function get it mean that this field is optional in body
                'size': object[2],              # size must be in Byte unit
                'is_ori':  True,
                'type_method': type_method,
                'gen_id': '',  # id of generation method
                'created_date': convert_current_date_to_iso8601()
            }
            ls_item_request.append(item_request)

        try:
            table = db_resource.Table(os.environ["T_DATA_ORI"])
            with table.batch_writer() as batch:
                for item in ls_item_request:
                    batch.put_item(Item=item)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        # update summary information
        try:
            response = db_client.update_item(
                TableName=os.environ["T_PROJECT_SUMMARY"],
                Key={
                    'project_id': {
                        'S': self.project_id
                    },
                    'type': {
                        'S': type_method
                    }
                },
                ExpressionAttributeNames={
                    '#SI': 'total_size',
                    '#COU': 'count',
                    '#TK': 'thu_key',
                    '#TN': 'thu_name'
                },
                ExpressionAttributeValues={
                    ':si': {
                        'N': str(total_size)
                    },
                    ':cou': {
                        'N': str(count)
                    },
                    ':tk': {
                        'S': ls_item_request[0]['s3_key']
                    },
                    ':tn': {
                        'S': ls_item_request[0]['filename']
                    }
                },
                UpdateExpression='SET #TK = :tk, #TN = :tn ADD #SI :si, #COU :cou',
            )
            print('response_summary: ', response)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        # update generate status
        try:
            table = db_resource.Table(os.environ['T_PROJECT'])
            response = table.update_item(
                Key={
                    'identity_id': self.identity_id,
                    'project_name': self.project_name,
                },
                ExpressionAttributeValues={
                    ':st': "FINISH",
                },
                UpdateExpression='SET  gen_status = :st'
            )
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        return convert_response(
            {
                'data': None,
                "error": False,
                "success": True,
                "message": None
            })


def lambda_handler(event, context):
    return AsyncCreateSample().handle(event=event, context=context)
