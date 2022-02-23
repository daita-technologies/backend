import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr
import time

from utils import convert_response, convert_current_date_to_iso8601
from balancer_utils import get_ec2_id_link_user, get_ec2_id_default

THRESHOLD_MINIMUM_IMAGES = 30

def _get_processing_image(table_ec2_task, ec2_id):
    response = table_ec2_task.query(
                                KeyConditionExpression=Key('ec2_id').eq(ec2_id),
                            )
    total_img = 0
    if response.get("Items"):
        for item in response["Items"]:
            total_img = total_img + item.get("num_img", 0)
            
    return total_img
    
def _is_ec2_running(ec2_resource, ec2_id):
    instance = ec2_resource.Instance(ec2_id)
    instance.load()
    if instance is None:
        raise Exception(f"Instance id {ec2_id} does not exist")
    else:
        return instance.state['Name'] == 'running'

def get_suitable_ec2(table_ec2, table_ec2_task, ec2_resource):
    # get list ec2 
    response = table_ec2.scan()
    print('response: ', response)
    ls_running = []
    ls_stop = []
    if response.get("Items"):
        for item in response["Items"]:
            if _is_ec2_running(ec2_resource, item["ec2_id"]):
                ls_running.append([item["ec2_id"]])
            else:
                ls_stop.append(item["ec2_id"])
    else:
        raise Exception("There is no ec2 in DB")

    if len(ls_running) == 0:
        return ls_stop[0]
    else:
        # update total images processing, ec2 = [<id>, <num_img>]
        for ec2 in ls_running:
            ec2.append(_get_processing_image(table_ec2_task, ec2[0]))
            
        #sorted ec2 following the processing images in running ec2
        ls_running = sorted(ls_running, key=lambda x: x[1])
        print('ls_running after sorted: ', ls_running)
        
        # check exist running ec2 has processing image smaller than threshold, 
        if ls_running[0][1]<THRESHOLD_MINIMUM_IMAGES:
            return ls_running[0][0]
            
        # check if exist stopped ec2 => assign to it
        if len(ls_stop)>0:
            return ls_stop[0]
            
        # if no stop and running bigger than threshold => assign to ec2 which has smallest processing image
        return ls_running[0][0]
    
def start_instance(instance):
    print('Instance id {ec2_id} stopped => start now')
    response = instance.start()
    instance.load()
    while instance.state['Name'] != 'running':
        if instance.state['Name'] == 'running':
            print('Running')
            pass
        else:
            time.sleep(5)
            instance.load()
            print('status: ', instance.state['Name'])
            pass
    
    return

def lambda_handler(event, context):

    # try to parse request body and check body fields
    try:
        print(event)
        identity_id = event["identity_id"]  
        task_id = event["task_id"]
        num_process_image = event["num_process_image"]

    except Exception as e:
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})

    try:
        db_resource = boto3.resource('dynamodb')
        table_ec2 = db_resource.Table(os.environ['T_INSTANCES'])
        table_ec2_task = db_resource.Table(os.environ['T_EC2_TASK'])
        ec2_resource = boto3.resource('ec2', region_name='us-east-2')
        
        # get suitable ec2 for running task
        ec2_id = get_suitable_ec2(table_ec2, table_ec2_task, ec2_resource)
        
        print("ec2 selected: ", ec2_id)
        
        # check already had the ec2 that linked with indentity_id
        # ec2_id = get_ec2_id_link_user(table, identity_id)
        # print("ec2_id: ",ec2_id)
        # if ec2_id is None:
        #     # get default
        #     ec2_id = get_ec2_id_default(table)            
        #     if ec2_id is None:
        #         raise Exception(f"This identity_id {identity_id} was not assigned to any ec2_id")
            
        # check instnace_id status
        instance = ec2_resource.Instance(ec2_id)
        if instance is None:
            raise Exception(f"Instance id {ec2_id} does not exist")
            
        print(instance.public_ip_address)
        ec2_info = {
            "ec2_id": ec2_id,
            "ip": instance.public_ip_address
        }
        
        # start instance whether the status of ec2 is stopped
        if instance.state['Name'] == 'stopped':
            start_instance(instance)
        elif instance.state['Name'] == 'stopping':
            # wait until ec2 status is stopped
            instance.load()
            while instance.state['Name'] != 'stopped':
                time.sleep(2)
                instance.load()
                pass
            
            print('Wait ec2 stopped to start')
            start_instance(instance)
        elif instance.state['Name'] == 'running':
            print('Instance id {ec2_id} running => no process')
            
        # update to DB ec2 status
        # response = table_ec2.update_item(
        #                             Key={
        #                                 "ec2_id": ec2_id,
        #                                 "assi_id": "free"
        #                             },
        #                             ExpressionAttributeValues = {
        #                                 ':st':  data_number,
        #                                 ':da': convert_current_date_to_iso8601(),
        #                             },
        #                             UpdateExpression = 'SET state = :st , time_update = :da'
        #                         )
        print('start ec2 ok!')
        
        # update to DB ec2_task
        response = table_ec2_task.put_item(
                                    Item={
                                        "ec2_id": ec2_id,
                                        "task_id": task_id,
                                        "num_img": num_process_image,
                                        "identity_id": identity_id,
                                        "created_time": convert_current_date_to_iso8601()
                                    }
                                )
        print("response add to DB: ", response)
        
            
    except Exception as e:
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
   
    return convert_response({'data': ec2_info, 
                            "error": False, 
                            "success": True, 
                            "message": None}
                        )