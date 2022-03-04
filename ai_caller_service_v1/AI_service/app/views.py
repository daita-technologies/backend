import os
import json
from re import L
import boto3
from django.db import models
from django.db.models import query
from django.shortcuts import render
import requests
import glob
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from .scripts.utils import request_update_proj , get_number_files , ThreadRequest, uploading_image , done_task_ec2 , insert_KV_EC2
from .scripts.dynamodb.task import TasksModel 
from .scripts.dynamodb.images import ImageLoader
from .scripts.dynamodb.methods import get_data_method
from .scripts.s3 import S3
import time 
from celery import shared_task,current_task
from celery.result import AsyncResult
import threading
import queue as Queue
from .scripts.logging_api import  logDebug , logInfo, logError

field_input =['id_token','project_name','augment_code','project_id','num_augments_per_image','identity_id']
image_loader = ImageLoader()
host = {
    'PREPROCESS':'http://{}:8000/ai',
    'AUGMENT':'http://{}:8000/ai'
}
try :
    method_db = get_data_method()
except Exception as e :
    logError.error("[ERROR] Error of get data from method table :{}\n".format(e))

@csrf_exempt
@api_view(('POST',))
def AI_service_request(request):
    data = json.loads(request.body)
    for it in field_input:
        if not it in data:
            return Response(status=status.HTTP_400_BAD_REQUEST,data={
                "message": "Miss "+str(it)+" parameter",
                "data": {},
                "error": False
            })
    res_dynamodb = manage_update_task.apply_async(queue='high',kwargs={'data':data})
    while not res_dynamodb.successful():
        time.sleep(0.1)
    test = res_dynamodb.get()
    data['project_prefix'] = test['project_prefix']
    res =  manage_task.apply_async(queue='low',kwargs={'data':data,'task_s3_id':test['task_s3_id'],'task_id':res_dynamodb.task_id,'num_images':test['num_images']})
    
    return Response(status=status.HTTP_200_OK,data={
        "message": "",
        "data": {'task_id':res_dynamodb.task_id},
        "error": True
        })

@csrf_exempt
@api_view(('POST',))
def AI_service_check_healthy(request):
    data = json.loads(request.body)
    if not 'task_id' in data:
        return Response(status=status.HTTP_400_BAD_REQUEST,data={
            "message": "Miss task_id parameter",
            "data": {},
            "error": True
        })
    res = AsyncResult(data['task_id'])
    
    return Response(status=status.HTTP_200_OK,data={
        "message": "",
        "data": {'status':res.state},
        "error": False
        })
"""
project_prefix
process_type
images
augment_code
task_id
"""
@shared_task
def download_s3_task(info_s3):
    info = {}
    s3_instance = S3(info_s3['project_prefix'],info_s3['process_type'])
    try:
        info = s3_instance.download_images(info_s3['images'],info_s3['augment_code'],info_s3['task_id'])
    except Exception as e:
        logError.debug("[ERROR] Task ID download images S3: {} - Error: {}\n".format(info_s3['task_id'],e))
        return  info
    return info 

@shared_task
def manage_update_task(data):
    
    task_id = current_task.request.id
    logInfo.debug("[INFO] Task ID: {} - Info: {}\n".format(task_id,data))
    
    try :
        info_image , err = image_loader({
            'id_token' : data['id_token'],
            'project_id' : data['project_id'],
            'augment_code': data['augment_code'],
            'data_number': data['data_number'],
            'data_type' : data['data_type'],
            'project_name': data['project_name']
        })
        if err != None:
            logError.error("[ERROR] Error image loader : {}".format(err))
            return 
    except Exception as e:
        logError.error("[ERROR] Error image loader : {}".format(e))
        return
    logDebug.debug("[DEBUG] info_image: {}".format(info_image['images']))
    project_prefix = info_image['project_prefix']
    images =  list(set(info_image['images']))

    augment_code =  data['augment_code']
    project_id = data['project_id']
    identity_id =  data['identity_id'] 
    process_type = 'AUGMENT' if 'AUG' in augment_code[0] else 'PREPROCESS'
    num_augments_per_image =  data['num_augments_per_image']



    # async task because of avoid timeout lambda 
    task_s3 = download_s3_task.apply_async(queue='download_image',kwargs={'info_s3':{
            'project_prefix' : project_prefix,
            'process_type' : process_type,
            'images' : images,
            'augment_code': augment_code,
            'task_id': task_id
    }})

    num_images = len(images)
    num_gens = num_images if process_type == 'PREPROCESS' else num_augments_per_image*num_images
    try :
        dynamodb = TasksModel()
        dynamodb.create_item(identity_id,task_id,project_id ,num_gens,process_type,"","")
    except Exception as e :
        logError.error("[ERROR] Task ID: {} - Dynamodb Create Task: {}\n".format(task_id,e))
        return

    return {"task_s3_id":task_s3.task_id,'num_gens':num_gens,'project_prefix':project_prefix,'num_images':num_images}
    
@shared_task
def manage_task(data,task_s3_id,task_id,num_images):
    dynamodb = TasksModel()
    id_token = data['id_token']
    project_prefix = data['project_prefix']
    project_name =  data['project_name']
    augment_code =  data['augment_code']
    project_id = data['project_id']
    identity_id =  data['identity_id'] 
    process_type = 'AUGMENT' if 'AUG' in augment_code[0] else 'PREPROCESS'
    num_augments_per_image =  data['num_augments_per_image']
    current_pwd = os.path.join('/home/ec2-user/efs',task_id)
    
    payload_getIP = json.dumps({"identity_id":data["identity_id"],"task_id":task_id,"num_process_image":num_images })

    # get IP

    IP = ''
    EC2_ID =  ''
    
    # update status preparing dynamodb : 
    ##PREPARING_HARDWARE update dynamodb#########
    dynamodb.update_process(task_id=task_id,identity_id=identity_id,num_finish=0,status='PREPARING_HARDWARE')
    logInfo.info("[INFO] TASK ID : {} UPDATE STATUS PREPARING_HARDWARE".format(task_id))
    ###############################################
    ##### Request lambda get IP
    try :
        client = boto3.client('lambda')
        response = client.invoke(
            FunctionName="staging-balancer-asy-get-ip",
            InvocationType="RequestResponse",
            Payload=payload_getIP
        )

        json_result = json.loads(response['Payload'].read())
        logDebug.debug("[DEBUG] Response staging-balancer-asy-get-ip: {}".format(json_result))
        logInfo.info("[INFO] staging-balancer-asy-get-ip: {}".format(json_result))
        body =json.loads(json_result['body'])
        logInfo.info("[INFO] staging-balancer-asy-get-ip body: {} and type : {}".format(json_result['body'],type(json_result['body'])))
        IP = body['data']['ip']
        EC2_ID =  body['data']['ec2_id']

    except Exception as e :
        logError.error("[ERROR] staging-balancer-asy-get-ip: {}".format(e))
        #update_process_error(task_id,identity_id,IP,EC2_ID)
        dynamodb.update_process_error(task_id=task_id,identity_id=identity_id,IP="",EC2_ID="")
        return {"message":"error"}
    ##############################################################
    # because front end check status after 5 second
    time.sleep(6)
    # fisinsh get IP

    ## prepare data S3 update dynamodb : PREPARING_DATA#########
    dynamodb.update_process(task_id=task_id,identity_id=identity_id,num_finish=0,status='PREPARING_DATA')
    logInfo.info("[INFO] TASK ID : {} UPDATE STATUS PREPARING_DATA".format(task_id))

    res_download_s3_task = AsyncResult(task_s3_id)
    while not res_download_s3_task.successful():
        time.sleep(0.01)
    # because front end check status after 5 second
    time.sleep(6)
    info = res_download_s3_task.get()
    logDebug.debug("[DEBUG] log res_download_s3_task {}".format(info))

    if not bool(info):
        logError.error("[ERROR] log res_download_s3_task is empty info")
        EC2_ID = "" if EC2_ID is None else EC2_ID
        dynamodb.update_process_error(task_id= task_id,identity_id= identity_id,IP=IP,EC2_ID=EC2_ID)
        return {"message":"error"}

    length_image =      info['images_download']
    batch_input  =      info['batch_input']  
    batch_output =      info['batch_output']
    batch_size   =      info['batch_size'] 

   
        
    # check EC2 get success 
    if  bool(EC2_ID):
        insert_KV_EC2(EC2_ID,task_id)
        logInfo.info('[INFO] insert_KV_EC2: Task id {} -  ec2 {}\n'.format(task_id,EC2_ID))

    # queue_req 
    queue_req=Queue.Queue(maxsize=0)
    # notice the task is finish and exit loop
    quit = Queue.Queue(maxsize=0)
    error_message_queue = Queue.Queue()
    # save log 
    log_request_AI = Queue.Queue()
    stop_update = False

    def AI_service():
        ai_request_queue = Queue.Queue()
        logInfo.debug("[INFO] TASK ID {} , request host {}".format(task_id,host[process_type].format(IP)))
        info = {
            'in_queue' : ai_request_queue,
            'augment_code' : augment_code,
            'num_augments_per_image' : num_augments_per_image,
            'id_token' : id_token,
            'project_id' : project_id, 
            'project_name' : project_name,
            'process_type': process_type,
            'identity_id' : identity_id,
            'error_message_queue': error_message_queue,
            'log_request_AI': log_request_AI,
            'host': host[process_type].format(IP)
        }
        
        for i in range(batch_size):
            w =  ThreadRequest(worker=info)
            w.setDaemon(True)
            w.start()
        
        for (inp , out) in zip(batch_input,batch_output):
            ai_request_queue.put((inp,out)) 
        ai_request_queue.join()
        quit.put({"Done":"test"})



    AI_req_thread = threading.Thread(target=AI_service)
    AI_req_thread.daemon = True
    AI_req_thread.start()
    combined = Queue.Queue(maxsize=0)
    
    def check_dir():
        gen_dir = os.path.join(current_pwd,'gen_images')
        total = length_image* num_augments_per_image if process_type == 'AUGMENT'  else length_image
        while True:
            length = get_number_files(gen_dir)
            ## length > 1 : update status RUNNING, check image exist#########

            if length > 0 :
                queue_req.put(length)

            if length == total:
                break
            if stop_update == True : break
            time.sleep(3)

    check_dir_thread = threading.Thread(target=check_dir)
    check_dir_thread.daemon = True
    check_dir_thread.start()
    
    def listen(q):
        while True:
            combined.put((q,q.get()))

    t1 = threading.Thread(target=listen,args=(queue_req,))
    t1.daemon =True 
    t1.start()
    t2 = threading.Thread(target=listen,args=(quit,))
    t2.daemon =True 
    t2.start()
    t3 = threading.Thread(target=listen,args=(error_message_queue,))
    t3.daemon =True 
    t3.start()
    t4 = threading.Thread(target=listen,args=(log_request_AI,))
    t4.daemon =True
    t4.start()
    # count_retries will count failed error from batch_output _request
    count_retries =  0
    while True:
        which , message =  combined.get()
        # receive the message from queue quit
        if which is quit:
            try :
                total = length_image* num_augments_per_image if process_type == 'AUGMENT'  else length_image
                dynamodb.update_process_uploading(task_id,identity_id)
                uploading_image({
                    'total_file': total,
                    'output_dir':  os.path.join(current_pwd,'gen_images'),
                    'project_prefix': project_prefix,
                    'method_db':method_db,
                    'process_type':process_type,
                    'list_aug':augment_code,
                    'info_request':{
                        'id_token' : id_token,
                        'project_id' : project_id,
                        'project_name' :project_name,
                        'identity_id' :identity_id
                    },
                })
                stop_update = True
                # if a request fail after retry state will reponse status is FINISH_ERROR
                if count_retries:
                    gen_dir = os.path.join(current_pwd,'gen_images')
                    num_finish = get_number_files(gen_dir)
                    dynamodb.update_process(task_id = task_id,identity_id=identity_id,num_finish= num_finish, status="FINISH_ERROR")
                else:
                    # complete update
                    dynamodb.update_finish(task_id,identity_id,total,IP,EC2_ID)
                logInfo.info('[INFO] Task ID: {} - {}\n'.format(task_id,"Success"))
                if bool(EC2_ID) :
                    logInfo.info('[INFO] done_task_ec2: Task id {} -  ec2 {}\n'.format(task_id,EC2_ID))
                    done_task_ec2(EC2_ID,task_id)
            except Exception  as e :
                logError.error('[ERROR] Task ID: {} - Fisnish Task: {}\n'.format(task_id,e))
                return {"Error":e}
            return {"complete" :message}
        # receive the message from thread request to update Tasks table
        elif which is queue_req:
            try :
                # update RUNNING #########
                # 
                dynamodb.update_process(task_id,identity_id,message,'RUNNING')
            except Exception  as e :
                dynamodb.update_process_error(task_id=task_id,identity_id=identity_id,IP=IP,EC2_ID=EC2_ID)
                logError.error('[ERROR] Task ID: {} - Update Process Task: {}\n'.format(task_id,e))
                return {"Error":e}
        # get error from error_message_queue
        elif which is error_message_queue:
            logError.error('[ERROR] TasK ID: - {} - {}\n'.format(task_id,message))
            if message == 'Error_retry':
                count_retries += 1
            logInfo.info("[INFO] error message Error_retry : {} batch_output : {}".format(count_retries,len(batch_output)))
            if count_retries < len(batch_output):
                continue
            stop_update = True
            try :
                dynamodb.update_process_error(task_id=task_id,identity_id=identity_id,IP=IP,EC2_ID=EC2_ID)
            except Exception as e :
                logError.error('[ERROR] Write Log Dynamodb error : {}'.format(e))
            if bool(EC2_ID):
                logInfo.info('[INFO] done_task_ec2: Task id {} -  ec2 {}\n'.format(task_id,EC2_ID))
                done_task_ec2(EC2_ID,task_id)
            return {"complete": "error"}
        elif which is  log_request_AI:
            logInfo.info("[INFO] Task ID {} ---- Request AI :{}".format(task_id,message))
    return {"complete" : "Finish"}