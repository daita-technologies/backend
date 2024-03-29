import time
import json
import boto3
import random
import os
import re
import tempfile
from datetime import datetime
from response import *
from utils import *
from identity_check import *
from ec2 import EC2Model, startEc2
from queue_request_AI import assignTaskToEc2
from models.task_model import TaskModel
from models.generate_task_model import GenerateTaskModel

from s3_utils import *
task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"], None)
generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])

ec2Model = EC2Model(os.environ["TABLE_LS_EC2"])
s3 = boto3.client('s3')


def split(uri):
    if not 's3' in uri[:2]:
        temp = uri.split('/')
        bucket = temp[0]
        filename = '/'.join([temp[i] for i in range(1, len(temp))])
    else:
        match = re.match(r's3:\/\/(.+?)\/(.+)', uri)
        bucket = match.group(1)
        filename = match.group(2)
    return bucket, filename


@error_response
def lambda_handler(event, context):
    inputJson = event['body']
    # with open(inputJson['path'],'r') as f:
    #     data = json.load(f)
    bucket, filename = split(inputJson['path'])
    resultS3 = s3.get_object(Bucket=bucket, Key=filename)
    data = json.loads(resultS3["Body"].read().decode())
    print("Event body: \n", data)
    downloadTask = data['download_task']
    #############Get ec2 free########################
    ec2FreeInstnaces = ec2Model.getFreeEc2()
    ################Start all ec2 free#####################
    # taskModel.create_item(identity_id=data['identity_id'],task_id=data['task_id'],project_id=data['project_id']
    #                                        ,num_gens=data['num_aug_per_imgs'] ,process_type=data['type_method'],IP='',EC2_ID='')
    # update num_gens for task
    task_model.update_attribute(data['task_id'], data['identity_id'], [
                                [TaskModel.FIELD_NUM_GENS_IMAGE, data["images"]]])
    task_model.update_generate_progress(
        task_id=data['task_id'], identity_id=data['identity_id'], num_finish=0, status='PREPARING_HARDWARE')

    list_request_ai = assignTaskToEc2(ec2Instances=ec2FreeInstnaces, data=downloadTask,
                                      num_augments_per_image=data['num_aug_per_imgs'],
                                      type_method=data['type_method'],
                                      code=data['ls_method_id'],
                                      reference_images=data[KEY_NAME_REFERENCE_IMAGES],
                                      is_normalize_resolution=data[KEY_NAME_IS_RESOLUTION],
                                      aug_parameters=data[KEY_NAME_AUG_PARAMS]
                                      )
    time.sleep(5)
    task_model.update_generate_progress(task_id=data['task_id'],
                                        identity_id=data['identity_id'],
                                        num_finish=0, status='RUNNING')
    s3.delete_object(Bucket=bucket, Key=filename)
    generate_task_model.init_messages_in_flight(
        identity_id=data['identity_id'], task_id=data['task_id'], )
    return {
        'state': 'Request_AI',
        'list_request_ai': list_request_ai,
        'identity_id': data['identity_id'],
        'id_token': data['id_token'],
        'task_id': data['task_id'],
        'project_prefix': data['project_prefix'],
        'current_num_retries': 0,
        'max_retries': 13,
        'is_retry': False,
        "project_id": data['project_id'],
        "project_name": data['project_name']
    }
