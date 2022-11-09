import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List
from utils import convert_current_date_to_iso8601, create_unique_id
from models.base_model import BaseModel

class AnnoDataModel(BaseModel):

    FIELD_PROJECT_ID        = "project_id"
    FIELD_FILENAME          = "filename"  
    FIELD_FILE_ID           = "file_id"  
    FIELD_CREATED_TIME      = "created_time"
    FIELD_UPDATED_TIME      = "updated_time"
    FIELD_GEN_ID            = "gen_id"
    FIELD_HASH              = "hash"    
    FIELD_IS_ORIGINAL       = "is_ori"
    FIELD_S3_KEY            = "s3_key"
    FIELD_TYPE_METHOD       = "type_method"
    FIELD_SIZE              = "size"
    FIELD_S3_SEGME_LABEL    = "s3_key_segm"     

    REQUEST_TYPE_ALL    = "all"

    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 

    def get_item(self, project_id, filename, ls_fields = []):
        if len(ls_fields)==0:
            ls_fields = [self.FIELD_FILENAME, self.FIELD_FILE_ID, self.FIELD_S3_KEY, self.FIELD_S3_SEGME_LABEL,
                        self.FIELD_SIZE, self.FIELD_CREATED_TIME]
        response = self.table.get_item(
            Key={
                self.FIELD_PROJECT_ID: project_id,
                self.FIELD_FILENAME: filename,
            },
            ProjectionExpression= ",".join(ls_fields)
        )
        item = response.get('Item', None)

        if item:
            item[self.FIELD_SIZE] = int(item[self.FIELD_SIZE])
        
        return item
        
    def _query_project_wo_healthcheck_id(self, project_id):
        response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                FilterExpression=Attr(self.FIELD_HEALTHCHECK_ID).not_exists()
            )
        items = response.get("Items", [])
        
        return items
    
    def _update_healthcheck_id(self, project_id, filename, healthcheck_id):
        response = self.table.update_item(
            Key={
                self.FIELD_PROJECT_ID: project_id,
                self.FIELD_FILENAME: filename,
            },
            ExpressionAttributeNames= {
                '#HC': self.FIELD_HEALTHCHECK_ID,
                '#UP_DATE': self.FIELD_UPDATED_TIME
            },
            ExpressionAttributeValues = {
                ':hc':  healthcheck_id,
                ':da': convert_current_date_to_iso8601(),                
            },
            UpdateExpression = 'SET #HC = :hc , #UP_DATE = :da'
        )
        return
        
    def get_all_wo_healthcheck_id(self, project_id: str):
        """
        get all data that does not have healthcheck_id
        Args:
            project_id (str): project id

        Returns:
            _type_: _description_
        """
        
        items = self._query_project_wo_healthcheck_id(project_id)
        
        ls_s3_key = [(item[self.FIELD_FILENAME], item[self.FIELD_S3_KEY]) for item in items]
        
        return ls_s3_key

    def get_all_data_in_project(self, project_id, ls_fields_projection = []):
        if len(ls_fields_projection) == 0:
            ls_fields_projection = [self.FIELD_FILENAME, self.FIELD_S3_KEY, 
                                    self.FIELD_SIZE]

        response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                ProjectionExpression=",".join(ls_fields_projection),
        )
        ls_items = response.get("Items", [])

        while 'LastEvaluatedKey' in response:
            next_token = response['LastEvaluatedKey']
            response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                ProjectionExpression=",".join(ls_fields_projection),
                ExclusiveStartKey=next_token
            )

            ls_items += response.get("Items", [])

        return [self.convert_decimal_indb_item(item) for item in ls_items]
    
    def update_healthcheck_id(self, project_id, filename, healthcheck_id):
        self._update_healthcheck_id(project_id, filename, healthcheck_id)

    def query_data_follow_batch(self, project_id, next_token, num_limit, ls_fields_projection=[]):
        if len(ls_fields_projection) == 0:
            ls_fields_projection = [self.FIELD_CREATED_TIME, self.FIELD_FILENAME, 
                                    self.FIELD_S3_KEY, self.FIELD_S3_SEGME_LABEL, self.FIELD_SIZE]

        if len(next_token) == 0:
            response = self.table.query(
                # IndexName='index-created-sorted',
                KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                ProjectionExpression= ",".join(ls_fields_projection),
                Limit = num_limit,
                ScanIndexForward = False
            )
            print('___Response first: ___', response)
        else:
            response = self.table.query(
                # IndexName='index-created-sorted',
                KeyConditionExpression = Key(self.FIELD_PROJECT_ID).eq(project_id),
                ProjectionExpression = ",".join(ls_fields_projection),
                ExclusiveStartKey=next_token,
                Limit=num_limit,
                ScanIndexForward=False
            )
            print('___Response next: ___', response)

        next_token = None
        # LastEvaluatedKey indicates that there are more results
        if 'LastEvaluatedKey' in response:
            next_token = response['LastEvaluatedKey']

        ls_items = response.get("Items", [])

        return next_token, [self.convert_decimal_indb_item(item) for item in ls_items]
    
    def delete_project(self,project_id):

        # delete in data
        query = None
        with self.table.batch_writer() as batch:
            while query is None or 'LastEvaluatedKey' in query:
                if query is not None and 'LastEvaluatedKey' in query:
                    query = self.table.query(
                        KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id),
                        ExclusiveStartKey=query['LastEvaluatedKey']
                    )
                else:
                    query = self.table.query(
                        KeyConditionExpression=Key(self.FIELD_PROJECT_ID).eq(project_id)
                    )
                
                for item in query['Items']:
                    batch.delete_item(
                            Key={
                                self.FIELD_PROJECT_ID: project_id,
                                self.FIELD_FILENAME: item[self.FIELD_FILENAME]
                            }
                        )

        return

    def get_item_from_list(self, project_id, ls_filename: List[str]):
        # create the batch request from input data
        ls_batch_request = []
        for filename in ls_filename:
            request = {
                self.FIELD_PROJECT_ID: project_id,  # partition key
                self.FIELD_FILENAME:  filename
            }
            ls_batch_request.append(request)

        batch_keys = {
            self.table.name: {
                'Keys': ls_batch_request,
                'ProjectionExpression': f'{self.FIELD_FILENAME}, {self.FIELD_SIZE}'
            }
        }

        response = boto3.resource('dynamodb').batch_get_item(RequestItems=batch_keys)["Responses"]

        ls_data_res = response.get(self.table.name, [])

        return self.convert_decimal_ls_item(ls_data_res)

    def put_item_from_ls_object(self, project_id, ls_object_info):
        # create the batch request from input data and summary the information
        ls_batch_request = []
        for object in ls_object_info:
            request = {
                self.FIELD_PROJECT_ID: project_id,  # partition key
                self.FIELD_S3_KEY: object['s3_key'],          # sort_key
                self.FIELD_FILENAME:  object['filename'],
                self.FIELD_FILE_ID: create_unique_id(),
                self.FIELD_HASH: object.get('hash', ''),   # we use function get it mean that this field is optional in body
                self.FIELD_SIZE: object['size'],  # size must be in Byte unit
                self.FIELD_IS_ORIGINAL: True,
                self.FIELD_CREATED_TIME: convert_current_date_to_iso8601()
            }
            ls_batch_request.append(request)

        # update data to DB
        # we use batch_write, it means that if key are existed in tables => overwrite
        with self.table.batch_writer() as batch:
            for item in ls_batch_request:
                batch.put_item(Item=item)

        return 

    def query_progress_ai_segm(self, project_id):
        """
        Check all data of a project, count total and the number of data that exist ai_segmentation
        """
        ls_fields_projection = [self.FIELD_FILENAME, self.FIELD_S3_SEGME_LABEL]

        ls_items = self.get_all_data_in_project(project_id, ls_fields_projection)
        ls_ai_finished = []

        for item in ls_items:
            if item.get(self.FIELD_S3_SEGME_LABEL) is not None:
                if len(item[self.FIELD_S3_SEGME_LABEL])>1:
                    ls_ai_finished.append(item)

        return len(ls_items), len(ls_ai_finished)


