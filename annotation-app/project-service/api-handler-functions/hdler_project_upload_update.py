import boto3
import json
import os
import uuid

from config import *
from response import *
from error_messages import *


from lambda_base_class import LambdaBaseClass

MAX_NUMBER_ITEM_PUT = 500
MAX_NUM_IMAGES_IN_ORIGINAL = 500
class ProjectAnnotationUploadUpdate(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
    def parser(self,body):
        self.id_token = body['id_token']
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
        
    def handle(self,event,context):
        self.parser(json.loads(event['body']))
        try:
            db_resource = boto3.resource("dynamodb")
            if self.is_ori:
                table = db_resource.Table(os.environ["TABLE_ANNO_PROJECT_SUMMARY"])
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
            else:
                num_final = 0

        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})

        db_client = boto3.client('dynamodb')
        db_resource = boto3.resource('dynamodb')
        try:
            table = os.environ["TABLE_ANNO_DATA_ORI"]

            table_pr = db_resource.Table(table)
            with table_pr.batch_writer() as batch:
                for item in self.ls_batch_request:
                    batch.put_item(Item=item)
        except Exception as e:
            print('Error: ', repr(e))
            return convert_response({"error": True,
                                    "success": False,
                                     "message": repr(e),
                                     "data": None})
        try:
            if self.is_ori and thumbnail_key is None:
                table = db_resource.Table(os.environ["TABLE_ANNO_PROJECT_SUMMARY"])
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
                    TableName=os.environ["TABLE_ANNO_PROJECT_SUMMARY"],
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

@error_response
def lambda_handler(event, context):
    return ProjectAnnotationUploadUpdate().handle(event=event,context=context)