import time
import json
import boto3
import random
import glob
import threading
import os
import queue
import re
from itertools import chain, islice
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *
from consts import ConstTbl
from models.task_model import TaskModel

task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"],None)
def batcher(iterable, size):
    iterator = iter(iterable)
    for first in iterator:
        yield list(chain([first], islice(iterator, size - 1)))
constModel = ConstTbl()

class S3(object):
    def __init__(self,project_prefix):
        self.s3 = boto3.client('s3')
        self.bucket = None
        self.s3_key =  None
        self.project_prefix =  project_prefix
        self.bucket , self.folder =  self.split(self.project_prefix)
        self.prefix_pwd = os.environ['EFSPATH']
        self.root_efs = os.environ['ROOTEFS']
    
    def split(self,uri):
        if not 's3' in uri[:2]:
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
        basename = os.path.basename(filename)
        new_image = os.path.join(folder,basename)        
        return new_image

    def download_images(self,images,task_id):

        taskDir = os.path.join(self.prefix_pwd,task_id)
        input_dir = os.path.join(taskDir,"raw_images")
        output_dir = os.path.join(taskDir,"gen_images")

        os.makedirs(input_dir,exist_ok=True)
        os.makedirs(output_dir,exist_ok=True)

        list_image = [self.download(it,input_dir) for it in images]
        def generator():
            yield from list_image
        batch_size =  int(constModel.get_num_value(code= 'limit_request_batchsize_ai', threshold='THRESHOLD'))
        batch_input = []
        batch_output = []
        total_len = 0
        jsonInputLoads = os.path.join(self.folder,'input_json')
        # os.makedirs(jsonInputLoads,exist_ok=True)
        for index,  batch in enumerate(batcher(generator(),batch_size)):
            output_dir_temp =  output_dir
            total_len += len(batch)
            jsonBatchImages = [self.root_efs+it for it in batch]
            # nameJsonBatches = os.path.join(jsonInputLoads,'input_batch_'+str(index)+'.json')
            # with open(nameJsonBatches,'w') as f:
            #     json.dump(jsonBatchImages,f)
            self.s3.put_object(
                Body=json.dumps(jsonBatchImages),
                Bucket= self.bucket,
                Key= os.path.join(jsonInputLoads,str(index)+'_download_image.json')
            )
            batch_input.append(self.bucket+'/'+jsonInputLoads+'/'+str(index)+'_download_image.json')
            nameoutput =  os.path.join(output_dir_temp,str(index))
            os.makedirs(nameoutput,exist_ok=True)
            batch_output.append(self.root_efs+nameoutput)
        download_images = []
        for index,it in enumerate(images):
            path ={'uri':it,'folder':input_dir}
            self.s3.put_object(
                Body=json.dumps(path),
                Bucket= self.bucket,
                Key= os.path.join(self.folder,str(index)+'_download_image.json')
            )
            download_images.append({'path':self.bucket+'/'+self.folder+'/'+str(index)+'_download_image.json'})
        info = {
            'images_download': len(list_image),
            'batches_input':  batch_input ,
            'batches_output':batch_output,
            'batch_size': batch_size,
        }
        return info , download_images


def downloadS3ToEFS(data):
    s3 = S3(project_prefix=data['project_prefix'])
    images = data['images']
    s3Resp, download_images = s3.download_images(images=images,task_id=data['task_id'])
    result = data
    result['download_task'] = s3Resp
    result['download_images'] = download_images
    return result


@error_response
def lambda_handler(event, context):
    body = json.loads(event['body'])

    print("body in event: ", body)
    data = body['data']
    task_model.update_generate_progress(task_id = data['task_id'], identity_id = data['identity_id'], num_finish = 0, status = 'PREPARING_DATA')
    result = downloadS3ToEFS(data)
    return  result