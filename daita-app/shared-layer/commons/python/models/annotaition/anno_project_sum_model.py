import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *


class AnnoProjectSumModel():

    FIELD_IDENTITY_ID = "identity_id"
    FIELD_PROJECT_ID = "project_id"
    FIELD_TYPE = "type"

    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name)

    def reset_prj_sum_preprocess(self, project_id, type_data):
        response = self.table.update_item(
            Key={
                self.FIELD_PROJECT_ID: project_id,
                self.FIELD_TYPE: type_data,
            },
            ExpressionAttributeNames={
                '#CO': 'count',
                '#TS': 'total_size'
            },
            ExpressionAttributeValues={
                ':ts':  0,
                ':co': 0
            },
            UpdateExpression='SET #TS = :ts, #CO = :co'
        )
        return response

    def update_project_sum(self, project_id, type_data, total_size, count, thu_key, thu_name):
        try:
            response = self.table.update_item(
                Key={
                    self.FIELD_PROJECT_ID: project_id,
                    self.FIELD_TYPE: type_data,
                },
                ExpressionAttributeNames={
                        '#SI': 'total_size',
                        '#COU': 'count',
                        '#TK': 'thu_key',
                        '#TN': 'thu_name'
                    },
                ExpressionAttributeValues={
                    ':si': total_size,
                    ':cou': count,
                    ':tk': thu_key,
                    ':tn': thu_name
                },
                UpdateExpression='SET #TK = :tk, #TN = :tn ADD #SI :si, #COU :cou'
            )
        except Exception as e:
            print('Error: ', repr(e))
            raise Exception(repr(e))

    def get_item(self, project_id, type_data):
        response = self.table.get_item(
            Key={
                'project_id': project_id,
                'type': type_data,
            }
        )
        print(response)
        if 'Item' in response:
            return response['Item']
        elif 'ResponseMetadata' in response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {'count': 0}
        return None
