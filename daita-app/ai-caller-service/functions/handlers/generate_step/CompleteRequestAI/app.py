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

def batcher(iterable, size):
    iterator = iter(iterable)
    for first in iterator:
        yield list(chain([first], islice(iterator, size - 1)))
# def invoke_sendmail_cognito_service(payload_body):
#     client = boto3.client('lambda')
#     payload_json = None 
#     try :
#         response = client.invoke(
#                 FunctionName="staging-project-upload-update",
#                 InvocationType="RequestResponse",
#                 Payload=json.dumps(payload_body)
#             )
#         payload_json = json.loads(response['Payload'].read())
#     except Exception as e:
#         return None , e
    
#     return payload_json , None 

def request_update_proj(update_pro_info,list_file_s3,gen_id):
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
                's3_key':os.path.join(update_pro_info['s3_key'],filename) ,
                'filename':filename,
                'hash':'',
                'size':info_file['size'],
                'is_ori':False,
                'gen_id' :gen_id 
            })     
        print("[DEBUG] Log Request Update Upload : {}\n".format(info))
        update_project_output = requests.post('https://nzvw2zvu3d.execute-api.us-east-2.amazonaws.com/staging/projects/upload_update',json=json.dumps(info))
    
        print("[DEBUG] Request Update Upload: {}\n".format(update_project_output.text))

@error_response
def lambda_handler(event, context):
    info_update_s3 = event['info_update_s3']
    
    def UpdateFunc(q):
        while True:
            info = q.get()
            try:
                request_update_proj(update_pro_info={
                        'identity_id': event['identity_id'],
                        'id_token':event['id_token'],
                        's3_key': event['project_prefix'],
                        'project_id': event['project_id'],
                        'project_name': event['project_name'],
                        'process_type': 'AUGMENT' if 'AUG' in event['gen_id'] else 'PREPROCESS'
                    },list_file_s3= info, gen_id=event['gen_id'])
            except Exception as e:
                print(e)
            q.task_done()
    
    # que = queue.Queue()
    # for i in range(10):
    #     worker = threading.Thread(target=UpdateFunc, args=(que,),daemon=True)
    #     worker.start()
    for info in info_update_s3:
        request_update_proj(update_pro_info={
                        'identity_id': event['identity_id'],
                        'id_token':event['id_token'],
                        's3_key': event['project_prefix'],
                        'project_id': event['project_id'],
                        'project_name': event['project_name'],
                        'process_type': 'AUGMENT' if 'AUG' in event['gen_id'] else 'PREPROCESS'
                    },list_file_s3= info, gen_id=event['gen_id'])
    # que.join()
    # if event['status'] == 'FINISH':
    #     folder = '/mnt/efs/'+ event['task_id']
    #     shutil.rmtree(folder)
    return {
        'task_id':event['task_id'],
        'identity_id':event['identity_id'],
        'status': event['status'],
        'state': 'FINISH'
    }