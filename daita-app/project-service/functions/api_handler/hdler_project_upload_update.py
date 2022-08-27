from lambda_base_class import LambdaBaseClass
import json
import boto3
import hashlib
import hmac
import base64
import os
from utils import convert_response, aws_get_identity_id, convert_current_date_to_iso8601

MAX_NUMBER_ITEM_PUT = 500
MAX_NUM_IMAGES_IN_ORIGINAL = 500

USERPOOLID = os.environ['COGNITO_USER_POOL']
CLIENTPOOLID = os.environ['COGNITO_CLIENT_ID']
IDENTITY_POOL = os.environ['IDENTITY_POOL']


def create_single_put_request(dict_value):
    dict_re = {
        'PutRequest': {
            'Item': {
            }
        }
    }
    for key, value in dict_value.items():
        dict_re['PutRequest']['Item'][key] = {
            value[0]: value[1]
        }
    return dict_re


def lambda_handler(event, context):
    return ProjectUploadUpdateCls().handle(event, context)


class ProjectUploadUpdateCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        id_token = body["id_token"]
        # self.client_events = boto3.client('events')  

        self.identity_id = aws_get_identity_id(
            id_token, USERPOOLID, IDENTITY_POOL)

        # get request data
        self.project_id = body['project_id']
        self.project_name = body['project_name']
        self.ls_object_info = body['ls_object_info']
        self.type_method = body.get('type_method', 'ORIGINAL')

        # check quantiy of items
        if len(self.ls_object_info) > MAX_NUMBER_ITEM_PUT:
            raise Exception(
                f'The number of items is over {MAX_NUMBER_ITEM_PUT}')
        if len(self.ls_object_info) == 0:
            raise Exception('The number of items must not empty')

        # create the batch request from input data and summary the information
        self.ls_batch_request = []
        self.total_size = 0
        self.count = 0
        self.total_process = len(self.ls_object_info)
        for object in self.ls_object_info:
            # update summary information
            size_old = object.get('size_old', 0)
            self.total_size += (object['size']-size_old)
            if size_old <= 0:
                self.count += 1

            self.is_ori = object['is_ori']
            request = {
                'project_id': self.project_id,  # partition key
                's3_key': object['s3_key'],          # sort_key
                'filename':  object['filename'],
                # we use function get it mean that this field is optional in body
                'hash': object.get('hash', ''),
                # size must be in Byte unit
                'size': object['size'],
                'is_ori': object['is_ori'],
                'type_method': self.type_method,
                'gen_id': object.get('gen_id', ''),  # id of generation method
                'created_date': convert_current_date_to_iso8601()
            }
            self.ls_batch_request.append(request)

    def handle(self, event, context):
        self.parser(json.loads(event['body']))
        # check number images in original must smaller than a limitation
        try:
            db_resource = boto3.resource("dynamodb")
            if self.is_ori:
                table = db_resource.Table(os.environ["TABLE_PROJECT_SUMMARY"])
                # get current data in original
                response = table.get_item(
                    Key={
                        "project_id": self.project_id,
                        "type": "ORIGINAL"
                    }
                )
                print('response get summary: ', response)
                if response.get('Item'):
                    current_num_data = response['Item'].get(
                        'num_exist_data', 0)
                    thumbnail_key = response['Item'].get('thu_key', None)
                else:
                    current_num_data = 0
                    thumbnail_key = None

                num_final = current_num_data + self.total_process
                # move check in upload_check
                # if num_final > MAX_NUM_IMAGES_IN_ORIGINAL:
                #     raise Exception(f'The total number in original data must smaller than {MAX_NUM_IMAGES_IN_ORIGINAL}! Current you already had {current_num_data}, but you tried to add {total_process} data.')
            else:
                num_final = 0

        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        # update data to DB
        # we use batch_write, it means that if key are existed in tables => overwrite
        db_client = boto3.client('dynamodb')
        db_resource = boto3.resource('dynamodb')
        type = None
        try:
            if self.is_ori:
                table = os.environ["T_DATA_ORI"]
                type = os.environ["T_DATA_ORI"]
            else:
                if self.type_method == 'PREPROCESS':
                    table = os.environ["T_DATA_PREPROCESS"]
                    type = os.environ["T_DATA_PREPROCESS"]
                elif self.type_method == 'AUGMENT':
                    table = os.environ["T_DATA_AUGMENT"]
                    type =  os.environ["T_DATA_AUGMENT"]
                else:
                    raise (Exception('Missing type_method parameters!'))

            table_pr = db_resource.Table(table)
            with table_pr.batch_writer() as batch:
                for item in self.ls_batch_request:
                    batch.put_item(Item=item)
            # response = db_client.batch_write_item(
            #     RequestItems = {
            #         table: ls_batch_request
            #     }
            # )
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})
        # self.client_events.put_events(
        #                 Entries=[
        #                     {
        #                         'Source': 'source.events',
        #                         'DetailType': 'lambda.event',
        #                         'Detail': json.dumps({
        #                             'project_id':self.project_id,
        #                             'type':type
        #                         }),
        #                         'EventBusName': os.environ["THUMBNAIL_EVENT_BUS"]
        #                     },
        #                 ]
        #             )
        # update summary information
        try:
            if self.is_ori and thumbnail_key is None:
                # update thumbnail key to project
                table = db_resource.Table(os.environ["TABLE_PROJECT_SUMMARY"])
                response = table.update_item(
                    Key={
                        'project_id': self.project_id,
                        'type': self.type_method,
                    },
                    ExpressionAttributeNames={
                        '#SI': 'total_size',
                        '#COU': 'count',
                        '#NE': 'num_exist_data',
                        '#TK': 'thu_key',
                        '#TN': 'thu_name'
                    },
                    ExpressionAttributeValues={
                        ':si': self.total_size,
                        ':cou': self.count,
                        ':ne': num_final,
                        ':tk': self.ls_batch_request[0]['s3_key'],
                        ':tn': self.ls_batch_request[0]['filename']
                    },
                    UpdateExpression='SET #NE = :ne, #TK = :tk, #TN = :tn ADD #SI :si, #COU :cou',
                )
            else:
                response = db_client.update_item(
                    TableName=os.environ["TABLE_PROJECT_SUMMARY"],
                    Key={
                        'project_id': {
                            'S': self.project_id
                        },
                        'type': {
                            'S': self.type_method
                        }
                    },
                    ExpressionAttributeNames={
                        '#SI': 'total_size',
                        '#COU': 'count',
                        '#NE': 'num_exist_data'
                    },
                    ExpressionAttributeValues={
                        ':si': {
                            'N': str(self.total_size)
                        },
                        ':cou': {
                            'N': str(self.count)
                        },
                        ':ne': {
                            'N': str(num_final)
                        }
                    },
                    UpdateExpression='SET #NE = :ne ADD #SI :si, #COU :cou',
                )
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        return convert_response({'data': {},
                                "error": False,
                                 "success": True,
                                 "message": None})
