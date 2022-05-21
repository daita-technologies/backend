
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
from s3_utils import split
from config import *
from response import *
from utils import *
from identity_check import *
s3 = boto3.client('s3')

@error_response
def lambda_handler(event, context):
    result = None
    for it in event:
        if isinstance(it,dict):
            result = it
    bucket ,folder =split(result['project_prefix'])
    s3.put_object(
        Body=json.dumps(result),
        Bucket= bucket,
        Key= os.path.join(folder,result['task_id']+'.json')
    )

    print("result: ", result)
    output = {  "path":bucket+'/'+folder+'/'+result['task_id']+'.json',
                "project_prefix":result["project_prefix"],
                "type_method":result["project_prefix"],
                "id_token": result["id_token"],
                "task_id": result["task_id"],
                "identity_id": result["identity_id"],
                "project_id": result["project_id"],
                "project_name": result["project_name"],
                "ls_method_id":result["ls_method_id"],
                "num_aug_per_imgs": result["num_aug_per_imgs"],
                KEY_NAME_REFERENCE_IMAGES: result[KEY_NAME_REFERENCE_IMAGES],
                KEY_NAME_IS_RESOLUTION: result[KEY_NAME_IS_RESOLUTION]
    }
    return output