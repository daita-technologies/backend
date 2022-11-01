import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *


class AnnoProjectSumModel():

    FIELD_IDENTITY_ID = "identity_id"
    FIELD_PROJECT_ID = "project_id"
    FIELD_TYPE = "type"
    FIELD_IS_DELETED = "is_dele"
    FIELD_UPDATED_DATE = "updated_date"
    FIELD_COUNT = "count"  ### total data in a project
    FIELD_TOTAL_SIZE = "total_size"
    FIELD_THUM_KEY = "thu_key"
    FIELD_THUM_FILENAME = "thu_name"
    FIELD_NUM_EXIST_DATA = "num_exist_data"


    VALUE_TYPE_ORIGINAL = "ORIGINAL"
    
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

    def get_current_number_data_in_prj(self, project_id, type_data = VALUE_TYPE_ORIGINAL):
        response = self.table.get_item(
            Key={
                self.FIELD_PROJECT_ID: project_id,
                self.FIELD_TYPE: type_data,
            }
        )

        if 'Item' in response:
            count = int(response['Item'].get(self.FIELD_COUNT, 0))
        else:
            count = 0

        return count

    def get_item_prj_sum_info(self, project_id, type_data = VALUE_TYPE_ORIGINAL, ls_fields_projection = []):
        if len(ls_fields_projection)==0:
            response = self.table.get_item(
                Key={
                    self.FIELD_PROJECT_ID: project_id,
                    self.FIELD_TYPE: type_data,
                }
                # ProjectionExpression= ",".join(ls_fields_projection)
            )
            # ls_fields_projection = [self.FIELD_COUNT, self.FIELD_TOTAL_SIZE, self.FIELD_THUM_KEY, self.FIELD_THUM_FILENAME]
        else:
            response = self.table.get_item(
                Key={
                    self.FIELD_PROJECT_ID: project_id,
                    self.FIELD_TYPE: type_data,
                },
                ProjectionExpression= ",".join(ls_fields_projection)
            )
        item = response.get('Item', None)
        
        return item


    def query_data_project_id(self, project_id):
        response = self.table.query(
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
            )
        
        return response.get("Items", [])

    def update_deleted_status(self, project_id, type_data):
        response = self.table.update_item(
            Key={
                self.FIELD_PROJECT_ID: project_id,
                self.FIELD_TYPE: type_data,
            },
            ExpressionAttributeNames={
                '#IS_DE': self.FIELD_IS_DELETED,
                '#UP_DATE': self.FIELD_UPDATED_DATE
            },
            ExpressionAttributeValues={
                ':is_de': True,  
                ':da': convert_current_date_to_iso8601(), 
            },
            UpdateExpression='SET #UP_DATE = :da, #IS_DE = :is_de'
        )

        return response

    def update_upload_new_data(self, project_id, total_size, count, num_final, 
                                thum_s3_key, thum_filename,  type_data = VALUE_TYPE_ORIGINAL):
        exp_att_name = {
            '#SI': self.FIELD_TOTAL_SIZE,
            '#COU': self.FIELD_COUNT,
            '#NE': self.FIELD_NUM_EXIST_DATA,
            '#TK': self.FIELD_THUM_KEY,
            '#TN': self.FIELD_THUM_FILENAME
        }
        exp_att_value = {
            ':si': total_size,
            ':cou': count,
            ':ne': num_final,
            ':tk': thum_s3_key,
            ':tn': thum_filename
        }

        response = self.table.update_item(
                    Key={
                        self.FIELD_PROJECT_ID: project_id,
                        self.FIELD_TYPE: type_data,
                    },
                    ExpressionAttributeNames = exp_att_name,
                    ExpressionAttributeValues = exp_att_value,
                    UpdateExpression = 'SET #NE = :ne, #TK = :tk, #TN = :tn ADD #SI :si, #COU :cou',
                )

        return