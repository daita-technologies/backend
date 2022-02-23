import json
import boto3
import hashlib
import hmac
import base64
import os
import uuid
import requests
import random
from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, convert_current_date_to_iso8601, aws_get_identity_id, dydb_get_project, dydb_update_project_data_type_number, dydb_update_class_data
import const

MAX_NUMBER_GEN_PER_IMAGES = 5


def lambda_handler(event, context):
    try:
        print(event['body'])
        body = json.loads(event['body'])
        id_token = body["id_token"]
        project_id = body['project_id']
        project_name = body['project_name']
        ls_methods_id = body['ls_method_id']
        data_type = body.get('data_type', 'ORIGINAL')  # type is one of ORIGINAL or PREPROCESS, default is original        
        num_aug_per_imgs = min(MAX_NUMBER_GEN_PER_IMAGES, body.get('num_aug_p_img', 1)) # default is 1
        data_number = body['data_number']  # array of number data in train/val/test  [100, 19, 1]
        
        if len(data_number)>0:
            if data_number[0] == 0:
                raise Exception("The number of training images must be greater than 0!")
        
        for number in data_number:
            if number<0:
                raise Exception('Number of train/val/test must greater than 0')
        
        if len(ls_methods_id) == 0:
            raise Exception('List method id must not empty!')

    except Exception as e:
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})

    try:
        identity_id = aws_get_identity_id(id_token)
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
    
    # get type of process
    type_method = 'PREPROCESS'
    if 'AUG' in ls_methods_id[0]:
        type_method = 'AUGMENT'
    elif 'PRE' in ls_methods_id[0]:
        type_method = 'PREPROCESS'
    else:
        raise(Exception('list method is not valid!'))
        
    # get const value
    try:
        MAX_TIMES_PREPROCESS_IMAGES = const.get_const_db(const.MAX_TIMES_PREPROCESS_IMAGES)
        MAX_TIMES_AUGMENT_IMAGES = const.get_const_db(const.MAX_TIMES_AUGMENT_IMAGES)
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})

    db_resource = boto3.resource('dynamodb') 
    # check any running tasks of this project
    try:
        table = db_resource.Table(os.environ["T_TASKS"])
        response = table.query(
                KeyConditionExpression=Key("identity_id").eq(identity_id),
                FilterExpression=Attr("project_id").eq(project_id) & Attr("status").ne("FINISH") & Attr("status").ne("ERROR")
            )
        print('get task running:' ,response.get("Items", []))
        if len(response.get("Items", [])) > 0:
            raise Exception("You have been running a task in this project, please wait!")
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
        
    
    try:
        # get project prefix
        infor = dydb_get_project(db_resource, identity_id, project_name)
        s3_prefix = infor['s3_prefix']
        times_generated = int(infor.get("times_generated", 0))
        times_preprocess = int(infor.get("times_propr", 0))
        
        # count time generate with AUGMENT
        if type_method == 'AUGMENT': 
            if times_generated>=MAX_TIMES_AUGMENT_IMAGES:
                raise Exception(const.MES_REACH_LIMIT_AUGMENT.format(MAX_TIMES_AUGMENT_IMAGES))
            this_times_generate = times_generated + 1
            
            print('this_times_augment: ', this_times_generate)
            
            # update data_type and data_number to project
            dydb_update_project_data_type_number(db_resource, identity_id, project_name, data_type, data_number, this_times_generate)
        else:
            this_times_generate = times_generated
            if times_preprocess>=MAX_TIMES_PREPROCESS_IMAGES:
                raise Exception(const.MES_REACH_LIMIT_PREPROCESS.format(MAX_TIMES_PREPROCESS_IMAGES))
            this_times_preprocess = times_preprocess + 1
            
            # update prj_sum_all of preprocess to 0
            table = db_resource.Table(os.environ["T_PROJECT_SUMMARY"])
            response = table.update_item(
                                    Key={
                                        'project_id': project_id,
                                        'type': type_method,
                                    },
                                    ExpressionAttributeNames= {
                                        '#CO': 'count',
                                        '#TS': 'total_size'
                                    },
                                    ExpressionAttributeValues = {
                                        ':ts':  0,
                                        ':co': 0
                                    },
                                    UpdateExpression = 'SET #TS = :ts, #CO = :co' 
                                )
            # update project the time preprocess
            table = db_resource.Table(os.environ['T_PROJECT'])
            response = table.update_item(
                Key={
                    'identity_id': identity_id,
                    'project_name': project_name,
                },
                ExpressionAttributeValues = {
                    ':da': convert_current_date_to_iso8601(),
                    ':tg': this_times_preprocess
                },
                UpdateExpression = 'SET updated_date = :da, times_propr = :tg' 
            )
            
        if project_id != infor['project_id']:
            raise Exception('project_id not match')
        
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})

    """==================================
    #### This part move to ai_caller_server
    ========================================
        
    if data_type == 'ORIGINAL':
        table_name = os.environ['T_DATA_ORI']
    elif data_type == 'PREPROCESS':
        table_name = os.environ['T_DATA_PREPROCESS']
    else:
        raise(Exception('data_type is not valid!'))
        
    if type_method == 'PREPROCESS':
        table_name = os.environ['T_DATA_ORI']
        
    # get list data
    table = db_resource.Table(table_name)
    response = table.query(
            KeyConditionExpression = Key('project_id').eq(project_id),
            ProjectionExpression='filename, s3_key',
        )
    ls_data = response['Items']
    
    if type_method == 'PREPROCESS':
        ls_process = [item['s3_key'] for item in ls_data] # use all data in original for preprocessing
    elif type_method == 'AUGMENT':
        random.shuffle(ls_data)
        ls_process = []
        ls_train = []
        ls_val = []
        ls_test = []
        for idx, data in enumerate(ls_data):
            if idx<data_number[0]:
                ls_train.append(data)
                ls_process.append(data['s3_key'])
                classtype = 'TRAIN'
            elif idx<data_number[0]+data_number[1]:
                ls_val.append(data)
                classtype = 'VAL'
            else:
                ls_test.append(data)
                classtype = 'TEST'
                
            # update category of data 
            dydb_update_class_data(table, project_id, data["filename"], classtype)
    """
    
    # send request to url  
    try:
        url = 'http://3.134.139.184:443/v1/api/request_ai'
        request_body = {
            "identity_id": identity_id,
            "id_token": id_token,
            # "images": ls_process,

            "project_id": project_id,
            "project_name": project_name,
            "augment_code": ls_methods_id,
            "num_augments_per_image": num_aug_per_imgs,

            "data_type" : data_type,  # add 
            "data_number" : data_number  # add
            # "project_prefix": s3_prefix
        }
        headers = { "Content-Type": "application/json" }
        response = requests.post(
            url,
            json= request_body,
            headers= headers,
        )
        value = response.json()
        print('response request: ', value)
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
    
    return convert_response(
            {
                'data': {
                        "task_id": value['data']['task_id'],
                        "times_generated": this_times_generate
                        },
                "error": False, 
                "success": True, 
                "message": None
            })
