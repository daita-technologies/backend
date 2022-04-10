import time
import json
import os
import boto3
import random
import shutil
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr
from task import TasksModel
 
taskModel = TasksModel()
@error_response
def lambda_handler(event, context):
    result = {'state': '',
                'reponse':'OK',
                'info_update_s3':[]}
    batches = event
    lenBatches =  len(batches)
    identity_id, task_id, gen_id ,project_id ,project_name= None, None, None,None , None
    task_finish = 0
    for  batch in batches:
        if identity_id == None:
            identity_id = batch['identity_id']
            task_id = batch['task_id']
            gen_id = batch['gen_id']
            project_id = batch['project_id']
            project_name = batch['project_name']
        if batch['response'] == 'OK':
            task_finish += 1
            outputBatch = '/mnt' + batch['output']
            shutil.rmtree(outputBatch)
            result['info_update_s3'].append(batch['info_upload_s3'])
    if task_finish == 0:
        result['status'] = 'ERROR'
        result['reponse'] = 'NOT_OK'
        result['state'] = 'ERROR'
    elif task_finish == lenBatches:
        result['status'] = 'FINISH'
        result['state'] = 'FINISH'
    else:
        result['status'] = 'FINISH_ERROR'
        result['state'] = 'FINISH'
    result['task_id'] = task_id
    result['identity_id'] = identity_id
    result['gen_id'] = gen_id
    result['project_id'] = project_id
    result['project_name'] = project_name
    return result
"""
task_id
identity_id
gen_id
info_update_s3:[
    {
        
    }
]
"""