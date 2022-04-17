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
        _ , filename =  self.split(uri)
        basename = os.path.basename(filename)
        new_image = os.path.join(folder,basename)
        return new_image
        # self.s3.download_file(bucket,filename,new_image)
        # print("IMAGE :",os.path.exists(new_image))


    def download_images(self,images,task_id):

        taskDir = os.path.join(self.prefix_pwd,task_id)
        input_dir = os.path.join(taskDir,"raw_images")
        output_dir = os.path.join(taskDir,"gen_images")

        os.makedirs(input_dir,exist_ok=True)
        os.makedirs(output_dir,exist_ok=True)

        # def downloadTask(q):
        #     while True:
        #         uri , folder = q.get()
        #         self.download(uri=uri,folder=folder)
        #         q.task_done()
        # que = queue.Queue()
        # for i in range(10):
        #     worker = threading.Thread(target=downloadTask, args=(que,),daemon=True)
        #     worker.start()
        # for it in images:
        #     que.put((it,input_dir))
        # que.join()
        
        # list_image = list(map(lambda x : x, list(glob.glob(input_dir+'/**'))))
        list_image = [self.download(it,input_dir) for it in images]
        def generator():
            yield from list_image
        batch_size =  int(constModel.get_num_value(code= 'limit_request_batchsize_ai', threshold='THRESHOLD'))
        batch_input = []
        batch_output = []
        total_len = 0
        
        for index,  batch in enumerate(batcher(generator(),batch_size)):
            output_dir_temp =  output_dir
            total_len += len(batch)
            batch_input.append([self.root_efs+it for it in batch])
            nameoutput =  os.path.join(output_dir_temp,str(index))
            os.makedirs(nameoutput,exist_ok=True)
            batch_output.append(self.root_efs+nameoutput)
        download_images = [{'uri':it,'folder':input_dir} for it in images]
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
    data = body['data']
    result = downloadS3ToEFS(data)
    return  result