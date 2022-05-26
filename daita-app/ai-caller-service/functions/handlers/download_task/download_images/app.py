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

s3 = boto3.client('s3')
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

def download(uri,folder):
    bucket, filename =  split(uri)
    basename = os.path.basename(filename)
    new_image = os.path.join(folder,basename)
    s3.download_file(bucket,filename,new_image)
    
@error_response
def lambda_handler(event, context):
    bucket , filename = split(event['task']['path'])
    resultS3 = s3.get_object(Bucket=bucket, Key=filename)
    data = json.loads(resultS3["Body"].read().decode())
    download(data['uri'],data['folder'])
    return {}