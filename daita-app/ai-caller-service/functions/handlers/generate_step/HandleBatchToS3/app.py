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
        bucket ,folder= split(project_prefix)
        temp_namefile =os.path.join(task_id,os.path.basename(it_img))
        s3_namefile = os.path.join(folder,temp_namefile)
        if not '.json' in it_img:
            info.append({'filename': s3_namefile,'size': os.path.getsize(it_img)})
            with open(it_img,'rb') as f :
                s3.put_object(Bucket=bucket,Key=s3_namefile,Body=f)
    return info

def UpdateStaskCurrentImageToTaskDB(task_id,identity_id,output):
    outputPath = Path(output)
    parrentFolder = outputPath.parent
    subfolders= [f.path for f in os.scandir(parrentFolder) if f.is_dir()]
    print("list subfolder: \n", subfolders)
    total_file = 0
    for folder in subfolders:
        total_file += get_number_files(folder)

    task_model.update_generate_progress(task_id = task_id, identity_id = identity_id, num_finish = total_file, status = "RUNNING")


@error_response
def lambda_handler(event, context):
    print(event)
    infoUploadS3 = []
    item = generate_task_model.get_task_info(event['identity_id'] ,event['task_id'])
    if event['response'] == 'OK' and item.status != 'CANCEL':
        outputBatchDir = '/'+  '/'.join(event['batch']['request_json']['output_folder'].split('/')[2:])
        outdir = glob.glob(outputBatchDir+'/*')

        print("OutputBatchDir: \n", outputBatchDir)
        print("outdir: \n", outdir)
        UpdateStaskCurrentImageToTaskDB(task_id= event['task_id'], identity_id=event['identity_id'] , output=outputBatchDir)
        infoUploadS3 =  UploadImage(output=outdir,project_prefix=event['project_prefix'],task_id=event['task_id'])
    return {
        'response': event['response'],
        'gen_id': str(event['batch']['request_json']['codes']),
        'output':event['batch']['request_json']['output_folder'],
        'info_upload_s3': infoUploadS3,
    }