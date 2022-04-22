import time
import json
import boto3
import random
import os
from datetime import datetime
from response import *
from utils import *
from identity_check import *
from ec2 import EC2Model, startEc2
from queue_request_AI import assignTaskToEc2
from models.task_model import TaskModel

task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"])

ec2Model = EC2Model()

"""
    download_task: 
        images_download:
        batched_input:
        batched_output:
        batch_size 
    output:
            state:
            list_request_ai :
                            [
                                {
                                    task_id
                                    batch_input:
                                    batch_out:
                                    api:
                                    project_prefix:
                                    identity_id:
                                    project_id:

                                }
                            ]
    """
@error_response
def lambda_handler(event, context):
    data = event['body']

    print("Event body: \n", data)
    downloadTask =  data['download_task']
    #############Get ec2 free########################
    ec2FreeInstnaces = ec2Model.getFreeEc2()
    ################Start all ec2 free#####################
    # taskModel.create_item(identity_id=data['identity_id'],task_id=data['task_id'],project_id=data['project_id']
    #                                        ,num_gens=data['num_aug_per_imgs'] ,process_type=data['type_method'],IP='',EC2_ID='')
    ### update num_gens for task
    task_model.update_attribute(data['task_id'], data['identity_id'], [[TaskModel.FIELD_NUM_GENS_IMAGE, len(data["images"])]])
    task_model.update_generate_progress(task_id = data['task_id'], identity_id = data['identity_id'], num_finish = 0, status = 'PREPARING_HARDWARE')

    ### assign code to [] with old flow
    ### TODO: check again when use choose option
    data['ls_method_id'] = []
    
    list_request_ai = assignTaskToEc2( ec2Instances=ec2FreeInstnaces,data= downloadTask,num_augments_per_image=data['num_aug_per_imgs'],type_method=data['type_method'],code=data['ls_method_id'])
    print(list_request_ai)
    return {
        'state': 'Request_AI',
        'list_request_ai':list_request_ai,
        'identity_id':data['identity_id'],
        'id_token': data['id_token'],
        'task_id': data['task_id'],
        'project_prefix': data['project_prefix'],
        'current_num_retries': 0,
        'max_retries': 12,
        'is_retry': False ,
        "project_id": data['project_id'],
        "project_name": data['project_name']
    }