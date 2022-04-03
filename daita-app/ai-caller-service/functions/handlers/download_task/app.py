from email.mime import image
import time
import json
import boto3
import random
import glob
import os
import re
from itertools import chain, islice
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *

def batcher(iterable, size):
    iterator = iter(iterable)
    for first in iterator:
        yield list(chain([first], islice(iterator, size - 1)))

class S3(object):
    def __init__(self,project_prefix):
        self.s3 = boto3.client('s3')
        self.bucket = None
        self.s3_key =  None
        self.project_prefix =  project_prefix
        self.bucket , self.folder =  self.split(self.project_prefix)
        self.prefix_pwd ='/mnt/efs'
    
    def split(self,uri):
        if not 's3' in uri:
            temp = uri.split('/')
            bucket = temp[0]
            filename = '/'.join([temp[i] for i in range(1,len(temp))])
        else:
            match =  re.match(r's3:\/\/(.+?)\/(.+)', uri)
            bucket = match.group(1)
            filename = match.group(2)
        return bucket, filename 

    def download(self,uri,folder):
        bucket , filename =  self.split(uri)
        print(bucket,filename)
        basename = os.path.basename(filename)
        new_image = os.path.join(folder,basename)
        result = self.s3.download_file(bucket,filename,new_image)
        print(result)
        if result:
            print('Download Success...')
        else:
            print('Ask Stack Overflow :/')


    def download_images(self,images,task_id):
        print(os.listdir(self.prefix_pwd))
        taskDir = os.path.join(self.prefix_pwd,task_id)
        input_dir = os.path.join(taskDir,"raw_images")
        output_dir = os.path.join(taskDir,"gen_images")

        os.makedirs(input_dir,exist_ok=True)
        os.makedirs(output_dir,exist_ok=True)
        
        for it in images:
            self.download(it,input_dir)
        list_image = list(glob.glob(input_dir+'/**'))
        
        def generator():
            yield from list_image
        batch_size =  8
        batch_input = []
        batch_output = []
        total_len = 0
        
        for index,  batch in enumerate(batcher(generator(),batch_size)):
            output_dir_temp =  output_dir
            total_len += len(batch)
            batch_input.append(batch)
            nameoutput =  os.path.join(output_dir_temp,str(index))
            os.makedirs(nameoutput,exist_ok=True)
            batch_output.append(nameoutput)

        info = {
            'images_download': len(list_image),
            'batch_input':  batch_input ,
            'batch_output':batch_output,
            'batch_size': batch_size
        }
        return info


def downloadS3ToEFS(data):
    s3 = S3(project_prefix=data['project_prefix'])
    images = data['images']
    s3Resp = s3.download_images(images=images,task_id=data['task_id'])
    result = data
    result['download_task'] = s3Resp
    return result


@error_response
def lambda_handler(event, context):
    body = json.loads(event['body'])
    data = body['data']
    result = downloadS3ToEFS(data)

    return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data = result
        )