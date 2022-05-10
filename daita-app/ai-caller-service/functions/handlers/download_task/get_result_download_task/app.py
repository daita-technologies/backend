
import time
import json
import boto3
import random
import glob
import threading
import os
import queue
import re
import json
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
    
@error_response
def lambda_handler(event, context):
    result = None
    for it in event:
        if isinstance(it,dict):
            result = it
    # path = os.path.join(os.environ['EFSPATH'],result['task_id'])
    # inputJson = os.path.join(path,'input.json')
    # with open(inputJson,'w') as f:
    #     json.dump(result,f)
    # output = {'path':inputJson}
    bucket ,folder =split(result['project_prefix'])
    s3.put_object(
        Body=json.dumps(result),
        Bucket= bucket,
        Key= os.path.join(folder,result['task_id']+'.json')
    )
    output = {  "path":bucket+'/'+folder+'/'+result['task_id']+'.json',
                "project_prefix":result["project_prefix"],
                "type_method":result["project_prefix"],
                "id_token": result["id_token"],
                "task_id": result["task_id"],
                "identity_id": result["identity_id"],
                "project_id": result["project_id"],
                "project_name": result["project_name"],
                "ls_method_id":result["ls_method_id"],
                "num_aug_per_imgs": result["num_aug_per_imgs"]
    }
    return output