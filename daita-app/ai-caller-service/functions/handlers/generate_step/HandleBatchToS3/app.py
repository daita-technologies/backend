import os
import re
import http
import time
import json
import boto3
import random
import glob
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *
from models.task_model import TaskModel
from models.generate_task_model import GenerateTaskModel

from pathlib import Path

task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"],None)
generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])

s3 = boto3.client('s3')
def is_img(img):
    return not os.path.splitext(img)[1] in ['.json']
def get_number_files(output_dir):
    img_list = []
    for r,_,f in os.walk(output_dir):
        for file in f:
            img_list.append(os.path.join(r,file))
    img_list = list(filter(is_img,img_list))
    return len(img_list)
def split(uri):
    if not 's3' in uri[:2]:
        temp = uri.split('/')
        bucket = temp[0]
        filename = '/'.join([temp[i] for i in range(1,len(temp))])
    else:
        match =  re.match(r's3:\/\/(.+?)\/(.+)', uri)
        bucket = match.group(1)
        filename = match.group(2)
    return bucket, filename
def UploadImage(output,project_prefix,task_id):
    info = []
    for it_img  in output:
        print(it_img)
        bucket ,folder= split(project_prefix)
        temp_namefile =os.path.join(task_id,os.path.basename(it_img))
        s3_namefile = os.path.join(folder,temp_namefile)
        if not '.json' in it_img:
            info.append({'filename': s3_namefile,'size': os.path.getsize(it_img)})
            with open(it_img,'rb') as f :
                s3.put_object(Bucket=bucket,Key=s3_namefile,Body=f)
        else:
            print(json.loads('it_img'))
    return info


@error_response
def lambda_handler(event, context):
    print(event)
    infoUploadS3 = []
    result = event
    
    result['info_upload_s3']= infoUploadS3
    
    if event.get("augment_codes", None) is not None:
        result['gen_id'] = str(event.get("augment_codes"))
    else:
        result['gen_id'] = str(event['batch']['request_json']['codes'])
    
    if event['response'] == 'OK' :
        if 'output_images' in event:
            output = list(map(lambda x : x.replace('/efs',''),event['output_images']))
            infoUploadS3 =  UploadImage(output=output,project_prefix=event['project_prefix'],task_id=event['task_id'])
        result['info_upload_s3'] = infoUploadS3
        
    return result