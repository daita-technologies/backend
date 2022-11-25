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
from lambda_base_class import LambdaBaseClass
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr
from models.generate_task_model import GenerateTaskModel
from models.task_model import TaskModel


class ComnpleteRequestAIClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.task_model = TaskModel(self.env.TABLE_GENERATE_TASK, None)
        self.generate_task_model = GenerateTaskModel(self.env.TABLE_GENERATE_TASK)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.info_upload_s3 = body["info_upload_s3"]
        self.identity_id = body["identity_id"]
        self.task_id = body["task_id"]
        self.id_token = body["id_token"]
        self.project_prefix = body["project_prefix"]
        self.project_id = body['project_id']
        self.project_name = body['project_name']
        self.gen_id = body["gen_id"]
        self.response = body["response"]
        self.num_finish = body.get("num_finish", -1)

    def batcher(self, iterable, size):
        iterator = iter(iterable)
        for first in iterator:
            yield list(chain([first], islice(iterator, size - 1)))

    def invokeUploadUpdateFunc(self, info):
        lambdaInvokeClient = boto3.client('lambda')
        payloadStr = json.dumps({'body': info})
        payloadBytesArr = bytes(payloadStr, encoding='utf8')
        
        lambdaInvokeReq = lambdaInvokeClient.invoke(
            FunctionName=self.env.FUNC_DAITA_UPLOAD_UPDATE,
            Payload=payloadBytesArr,
            InvocationType="RequestResponse",
        )
        payload = json.loads(lambdaInvokeReq['Payload'].read())
        print("Payload response: ", payload)
        body = json.loads(payload['body'])
        return body


    def request_update_proj(self, update_pro_info, list_file_s3, gen_id,task_id):
        batch_list_s3 = list(self.batcher(list_file_s3,20))
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
            
            update_project_output = self.invokeUploadUpdateFunc(info)
            print("[DEBUG] Request Update Upload: {}\n".format(update_project_output))

    def handle(self, event, context):
        ### parse body
        self.parser(event, is_event_as_body=True)

        item = self.generate_task_model.get_task_info(self.identity_id, self.task_id)
        resq = self.request_update_proj(update_pro_info={
                                            'identity_id': self.identity_id,
                                            'id_token': self.id_token,
                                            's3_key': self.project_prefix,
                                            'project_id': self.project_id,
                                            'project_name': self.project_name,
                                            'process_type': item.process_type
                                        }, 
                                        list_file_s3 = self.info_upload_s3, 
                                        gen_id = self.gen_id, 
                                        task_id = self.task_id)
        
        
        if self.num_finish<0:
            pass
        else:    
            self.task_model.update_number_files(task_id = self.task_id, identity_id = self.identity_id,
                                            num_finish = self.num_finish)

        return {
            'response': self.response
        }

@error_response
def lambda_handler(event, context):
    return ComnpleteRequestAIClass().handle(event=event,  context=context)