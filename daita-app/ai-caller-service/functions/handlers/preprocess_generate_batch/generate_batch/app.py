from curses import keyname
import time
import json
import os
import boto3
import random
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr
from models.generate_task_model import GenerateTaskModel
from models.task_model import TaskModel

TBL_data_original = os.getenv("TableDataOriginalName")
TBL_data_proprocess = os.getenv("TableDataPreprocessName")
TBL_PROJECT = os.getenv("TableProjectsName")
MAX_NUMBER_GEN_PER_IMAGES = 5
generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])
task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"],None)

def dydb_update_project_data_type_number(db_resource, identity_id, project_name, data_type, data_number, times_generated):
    try:
        table = db_resource.Table(TBL_PROJECT)
        response = table.update_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ExpressionAttributeNames= {
                '#DA_TY': data_type
            },
            ExpressionAttributeValues = {
                ':va':  data_number,
                ':da': convert_current_date_to_iso8601(),
                ':tg': times_generated
            },
            UpdateExpression = 'SET #DA_TY = :va , updated_date = :da, times_generated = :tg'
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise
    if response.get('Item', None):
        return response['Item']
    return None

def dydb_get_project(db_resource, identity_id, project_name):
    try:
        table = db_resource.Table(TBL_PROJECT)
        response = table.get_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ProjectionExpression= 'project_id, s3_prefix, times_generated'
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise
    if response.get('Item', None):
        return response['Item']
    return None
def dydb_update_class_data(table, project_id, filename, classtype):
    response = table.update_item(
            Key={
                'project_id': project_id,
                'filename': filename,
            },
            ExpressionAttributeNames= {
                '#CT': 'classtype',
            },
            ExpressionAttributeValues = {
                ':ct':  classtype,

            },
            UpdateExpression = 'SET #CT = :ct'
        )

class ImageLoader(object):
    def __init__(self):
        self.db_resource = boto3.resource('dynamodb')
    '''
    info_image:
                identity_id
                project_id
                augment_code
                data_number
                data_type
                project_name
    '''
    def __call__(self,info_image):
        identity_id = info_image['identity_id']
        project_id = info_image['project_id']
        ls_methods_id =  info_image['ls_method_id']
        project_name = info_image['project_name']
        data_type = info_image['data_type']
        data_number = info_image['data_number']
        # get type of process
        type_method = info_image[KEY_NAME_PROCESS_TYPE]

        infor = dydb_get_project(self.db_resource, identity_id, project_name)
        s3_prefix = infor['s3_prefix']

        if data_type == 'ORIGINAL':
            table_name = TBL_data_original
        elif data_type == 'PREPROCESS':
            table_name = TBL_data_proprocess
        else:
            raise(Exception('data_type is not valid!'))

        if type_method == 'PREPROCESS':
            table_name = TBL_data_original

        # get list data
        table = self.db_resource.Table(table_name)
        response = table.query(
                KeyConditionExpression = Key('project_id').eq(project_id),
                ProjectionExpression='filename, s3_key',
            )
        ls_data = response['Items']

        if type_method == 'PREPROCESS':
            ls_process = [item['s3_key'] for item in ls_data] # use all data in original for preprocessing
        elif type_method == 'AUGMENT':
            random.shuffle(ls_data)
            ls_process = []
            ls_train = []
            ls_val = []
            ls_test = []
            for idx, data in enumerate(ls_data):
                if idx<data_number[0]:
                    ls_train.append(data)
                    ls_process.append(data['s3_key'])
                    classtype = 'TRAIN'
                elif idx<data_number[0]+data_number[1]:
                    ls_val.append(data)
                    classtype = 'VAL'
                else:
                    ls_test.append(data)
                    classtype = 'TEST'

                dydb_update_class_data(table, project_id, data["filename"], classtype)
        return {"images": ls_process, "project_prefix":s3_prefix, 'type_method':type_method}

@error_response
def lambda_handler(event, context):
    print("START PREPARE STATE")
    print(event)
    body = event['ori2']['Execution']['Input']['detail']
    exceArn = event['abcd']
    generate_task_model.update_ExecutionArn(
        identity_id=body['identity_id'], task_id=body['task_id'],executionArn=exceArn
    )
    task_model.update_generate_progress(task_id = body['task_id'], identity_id = body['identity_id'], num_finish = 0, status = 'PREPARING_DATA')

    imageLoad = ImageLoader()
    data = imageLoad(body)
    data['id_token'] = body['id_token']
    data['task_id'] = body['task_id']
    data['identity_id'] = body['identity_id']
    data['project_id'] = body['project_id']
    data['project_name'] = body['project_name']
    data['ls_method_id'] = body['ls_method_id']
    data['num_aug_per_imgs'] = body['num_aug_per_imgs'] if 'num_aug_per_imgs' in body else 1
    data[KEY_NAME_PROCESS_TYPE] = body[KEY_NAME_PROCESS_TYPE]
    data[KEY_NAME_REFERENCE_IMAGES] = body[KEY_NAME_REFERENCE_IMAGES]
    data[KEY_NAME_IS_RESOLUTION] = body[KEY_NAME_IS_RESOLUTION]
    data[KEY_NAME_AUG_PARAMS] = body[KEY_NAME_AUG_PARAMS]

    return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=data
        )
