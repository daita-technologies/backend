import shutil
import time
import json
import boto3
import random
from datetime import datetime
import requests
import queue
import threading
from itertools import chain, islice
import os
from config import *
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr
from models.generate_task_model import GenerateTaskModel
from models.task_model import TaskModel
task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"],None)
generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])
def batcher(iterable, size):
    iterator = iter(iterable)
    for first in iterator:
        yield list(chain([first], islice(iterator, size - 1)))

def request_update_proj(update_pro_info,list_file_s3,gen_id,task_id):
    batch_list_s3 = list(batcher(list_file_s3,20))
    for batch_file in batch_list_s3:
        print("[DEBUG] batch file {}".format(batch_file))
        info = {'identity_id':update_pro_info['identity_id'], 
                'id_token':update_pro_info['id_token'] ,
                'project_id':update_pro_info['project_id'],
                'project_name':update_pro_info['project_name'],
                'type_method': update_pro_info['process_type'],
                'ls_object_info':[]}    
        for info_file in batch_file:
            filename = os.path.basename(info_file['filename'])
            info['ls_object_info'].append({
                's3_key':os.path.join(update_pro_info['s3_key'],os.path.join(task_id,filename)) ,
                'filename':filename,
                'hash':'',
                'size':info_file['size'],
                'is_ori':False,
                'gen_id' :gen_id 
            })     
        print("[DEBUG] Log Request Update Upload : {}\n".format(info))
        update_project_output = requests.post('https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/projects/upload_update',json=info)
    
        print("[DEBUG] Request Update Upload: {}\n".format(update_project_output.text))


@error_response
def lambda_handler(event, context):
    print(event)
    for record in event['Records']:
        print(record)
        body =  json.loads(record['body'])
        info_upload_s3 = body['info_upload_s3']
        item = generate_task_model.get_task_info(body['identity_id'] ,body['task_id'])
        
        request_update_proj(update_pro_info={
                        'identity_id': body['identity_id'],
                        'id_token':body['id_token'],
                        's3_key': body['project_prefix'],
                        'project_id': body['project_id'],
                        'project_name': body['project_name'],
                        'process_type': item.process_type
                    },list_file_s3= info_upload_s3, gen_id=body['gen_id'],task_id=body['task_id'])
        db_resource = boto3.resource('dynamodb',REGION)
    
        if item.process_type == 'AUGMENT':
            table = db_resource.Table(os.environ['TABLE_DATA_AUGMENT'])
        elif item.process_type == 'PREPROCESS':
            table = db_resource.Table(os.environ['TABLE_DATA_PREPROCESS'])
        
        queryResponse = table.query(
            KeyConditionExpression=Key('project_id').eq(body['project_id']),
             FilterExpression=Attr('s3_key').contains(body['task_id'])
            )
        print(queryResponse)
        task_model.update_number_files(task_id = body['task_id'], identity_id = body['identity_id'],
         num_finish = len(queryResponse['Items']))

    return {}