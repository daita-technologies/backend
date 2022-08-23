from lambda_base_class import LambdaBaseClass
import json
import boto3
import hashlib
import hmac
import base64
import os
from utils import convert_response, aws_get_identity_id


MAX_NUMBER_ITEM_QUERY = 1000
MAX_NUM_IMAGES_IN_ORIGINAL = 1000
USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


def lambda_handler(event, context):
    return ProjectUploadCheckCls().handle(event, context)


class ProjectUploadCheckCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.id_token = body["id_token"]
        self.project_id = body["project_id"]
        self.ls_filename = body["ls_filename"]

        # check quantiy of items
        if len(self.ls_filename) > MAX_NUMBER_ITEM_QUERY:
            raise Exception(
                f'The number of items is over {MAX_NUMBER_ITEM_QUERY}')

        # create the batch request from input data
        self.ls_batch_request = []
        for object in self.ls_filename:
            request = {
                'project_id': {'S': self.project_id},  # partition key
                'filename': {'S': object}
            }
            self.ls_batch_request.append(request)

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        # get identity_id from id token, also check the authentication from client
        try:
            identity_id = aws_get_identity_id(
                self.id_token, USERPOOLID, IDENTITY_POOL)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        # query data from DB
        try:
            db_client = boto3.client('dynamodb')
            ls_data = []
            start_idx = 0
            while start_idx < len(self.ls_batch_request):
                next_idx = start_idx + 50
                response = db_client.batch_get_item(
                    RequestItems={
                        os.environ["T_DATA_ORI"]: {
                            'Keys': self.ls_batch_request[start_idx:next_idx],
                            'ProjectionExpression': 'filename, size'
                        }
                    }
                )
                start_idx = next_idx
                print(start_idx, next_idx)
                for data in response['Responses'][os.environ["T_DATA_ORI"]]:
                    ls_data.append(
                        {'filename': data['filename']['S'], 'size': data['size']['N']})

            print(ls_data)

            # check available image is over the limitation
            db_resource = boto3.resource("dynamodb")
            table = db_resource.Table(os.environ["T_PROJECT_SUMMARY"])
            response = table.get_item(
                Key={
                    "project_id": self.project_id,
                    "type": "ORIGINAL"
                }
            )
            if response.get('Item'):
                current_num_data = response['Item'].get('count', 0)
            else:
                current_num_data = 0
            if len(self.ls_batch_request)-len(ls_data)+current_num_data > MAX_NUM_IMAGES_IN_ORIGINAL:
                raise (Exception(
                    f'The number of images in original of project is over the limitation {MAX_NUM_IMAGES_IN_ORIGINAL}!'))

        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        return convert_response({
            'data': ls_data,
            "error": False,
            "success": True,
            "message": None
        })
