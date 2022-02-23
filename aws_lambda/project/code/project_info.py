import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id, dydb_get_project_id, dydb_get_project_full

def lambda_handler(event, context):
    try:
        print(event['body'])
        body = json.loads(event['body'])
        id_token = body["id_token"]
        project_name = body["project_name"]
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

    db_resource = boto3.resource('dynamodb')
    #get project_id
    try:
        table = db_resource.Table(os.environ['T_PROJECT'])
        res_project = dydb_get_project_full(table, identity_id, project_name)
        
        # print(res_projectid)
        res_projectid = res_project['project_id']
        is_sample = res_project.get("is_sample", False)
        gen_status = res_project.get("gen_status", "FINISH")  # default is finish, else GENERATING
        res_times_generated = int(res_project.get('times_generated', 0))
        
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
    
    # get info detail of a project
    try:
        table =  db_resource.Table(os.environ['T_PROJECT_SUMMARY'])       
        response = table.query(            
            KeyConditionExpression=Key('project_id').eq(res_projectid),           
        )
        # print(response)
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
    
    if response.get('Items', None):
        groups = {}
        for item in response['Items']:
            type = item['type']
            data_num = res_project.get(type, None) 
            if data_num is not None:
                data_num = [int(a) for a in data_num]
            groups[type] = {
                'count': int(item['count']),
                'size' : int(item['total_size']),
                'data_number': data_num
            }
            
        # get running tasks of project
        ls_task = []
        table = db_resource.Table(os.environ['T_TASKS'])
        items_task = table.query(                
                ProjectionExpression='project_id, task_id',
                KeyConditionExpression=Key('identity_id').eq(identity_id),
                FilterExpression=Attr('status').ne('FINISH') & Attr('status').ne('ERROR')               
            )
        if items_task.get('Items'):
            for item_task in items_task['Items']:
                if item_task.get('project_id', '') == res_projectid:  
                    ls_task.append(item_task.get('task_id', ''))
        
        return convert_response({'data': {
                    "identity_id": identity_id,
                    "project_name": project_name,
                    "project_id": res_projectid,
                    "times_generated": res_times_generated,
                    "is_sample": is_sample,
                    "gen_status": gen_status,
                    "ls_task": ls_task,
                    "groups": groups,
                }, 
            "error": False, 
            "success": True, 
            "message": None})
    else:
        return convert_response({'data': {                
                    "identity_id": identity_id,
                    "project_name": project_name,
                    "project_id": res_projectid,
                    "times_generated": res_times_generated,
                    "is_sample": is_sample,
                    "gen_status": gen_status,
                    "ls_task": [],
                    "groups": None
                },
            "error": False, 
            "success": True, 
            "message": None})
    
