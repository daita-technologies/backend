import time
import json
import os
import boto3
import random
import shutil
import glob
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr

@error_response
def lambda_handler(event, context):
    result = {'state': '',
                'response':'OK',
                'info_update_s3':[]}
    batches = event
    lenBatches =  len(batches)
    # identity_id, task_id, gen_id ,project_id ,project_name , id_token,project_prefix= None, None, None,None , None, None,None
    task_finish = 0
    for  batch in batches:
        result['gen_id'] = batch['gen_id']
        # if identity_id == None:
        #     identity_id = batch['identity_id']
        #     task_id = batch['task_id']
        #     gen_id = batch['gen_id']
        #     project_id = batch['project_id']
        #     project_name = batch['project_name']
        #     id_token = batch['id_token']
        #     project_prefix = batch['project_prefix']
        if batch['response'] == 'OK':
            task_finish += 1
            outputBatch = '/'+  '/'.join(batch['output'].split('/')[2:])
            # batch['output'] 
            #'/'+  '/'.join(event['batch']['request_json']['output_folder'].split('/')[2:])
            print(glob.glob(outputBatch+'/**'))
            shutil.rmtree(outputBatch)
            result['info_update_s3'].append(batch['info_upload_s3'])
        
    if task_finish == 0:
        result['status'] = 'ERROR'
        result['response'] = 'NOT_OK'
        result['state'] = 'ERROR'
    elif task_finish == lenBatches:
        result['status'] = 'FINISH'
        result['state'] = 'FINISH'
    else:
        result['status'] = 'FINISH_ERROR'
        result['state'] = 'FINISH'
    return result