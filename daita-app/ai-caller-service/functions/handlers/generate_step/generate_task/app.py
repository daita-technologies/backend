import time
import json
import boto3
import random
from datetime import datetime
from response import *
from utils import *
from identity_check import *
from boto3.dynamodb.conditions import Key, Attr
from task import TasksModel
from ec2 import EC2Model, startEc2
from queue_request_AI import assignTaskToEc2
taskModel = TasksModel()
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
    downloadTask =  data['download_task']
    #############Get ec2 free########################
    ec2FreeInstnaces = ec2Model.getFreeEc2()
    ################Start all ec2 free#####################
    taskModel.create_item(identity_id=data['identity_id'],task_id=data['task_id'],project_id=data['project_id']
                                           ,num_gens=data['num_aug_per_imgs'] ,process_type=data['type_method'],IP='',EC2_ID='')
    try:
        for ec2 in ec2FreeInstnaces:
            # print(ec2['ec2_id'])
            startEc2(ec2['ec2_id'])
    except Exception as e:
        print(e)
        raise e
    ##### assign ec2###########################
    taskModel.update_process(task_id=data['task_id'],identity_id=data['identity_id'],num_finish=0,status='PREPARING_HARDWARE')
    list_request_ai = assignTaskToEc2( ec2Instances=ec2FreeInstnaces,data= downloadTask,num_augments_per_image=data['num_aug_per_imgs'],type_method=data['type_method'],code=data['ls_method_id'])
    print(list_request_ai)
    return {
        'state': 'Request_AI',
        'list_request_ai':list_request_ai,
        'identity_id':data['identity_id'],
        'task_id': data['task_id'],
        'project_prefix': data['project_prefix'],
        'current_num_retries': 0,
        'max_retries': 12,
        'is_retry': False ,
        "project_id": data['project_id'],
        "project_name": data['project_name']
    }