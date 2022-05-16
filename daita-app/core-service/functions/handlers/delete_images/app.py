import json
import boto3
import hashlib
import hmac
import base64
import os

from boto3.dynamodb.conditions import Key, Attr
from utils import convert_response, aws_get_identity_id, get_table_dydb_object, dydb_update_prj_sum

MAX_NUMBER_ITEM_DELETE = 100


def delete_image_healthycheck_info(db_resource,project_id,healthcheck_id):
    table_healthycheck_info = db_resource.Table(os.environ['TABLE_HEALTHCHECK_INFO'])
    table_healthycheck_info.delete_item(
                                Key = {
                                    'project_id': project_id,
                                    'healthcheck_id': healthcheck_id
                                }
                            )    

def lambda_handler(event, context):
    try:
        print(event['body'])
        body = json.loads(event['body'])

        #check authentication
        id_token = body["id_token"]
        identity_id = aws_get_identity_id(id_token)

        #get request data
        project_id = body['project_id']
        ls_object_info = body['ls_object_info']

        # check quantiy of items
        if len(ls_object_info)>MAX_NUMBER_ITEM_DELETE:
            raise Exception(f'The number of items is over {MAX_NUMBER_ITEM_DELETE}')

        #create the batch request from input data and summary the information
        dict_request = {}
        
        for object in ls_object_info:
            type_method = object['type_method']
            if dict_request.get(type_method) is None:
                dict_request[type_method] = {
                    'ts': 0,
                    'count': 0,
                    'project_id': project_id,
                    'ls_rq': []
                }
            # update summary information
            dict_request[type_method]['ts'] += object['size']
            dict_request[type_method]['count'] = dict_request[type_method]['count'] + 1
            request = {
                'filename': object['filename']
            }
            dict_request[type_method]['ls_rq'].append(request)
    except Exception as e:
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})

    # update data to DB 
    # we use batch_write, it means that if key are existed in tables => overwrite
    db_resource = boto3.resource('dynamodb')
    try:
        table_sum_all = db_resource.Table(os.environ['T_PROJECT_SUMMARY'])
        for key, value in dict_request.items():
            
            project_id = value['project_id']
            
            # delete in data table
            table = get_table_dydb_object(db_resource, key)
            for request in value['ls_rq']:
                item = table.get_item(Key={
                    'project_id': project_id,
                    'filename': request['filename']
                })
                if not item['healthcheck_id'] is None or  isinstance(item['healthcheck_id'],str):
                    delete_image_healthycheck_info(db_resource=db_resource,project_id=project_id,healthcheck_id=item['healthcheck_id'])
                table.delete_item(Key={
                    'project_id': project_id,
                    'filename': request['filename']
                })

            # if we delete in original, we also delete in preprocess
            if key == "ORIGINAL":
                table = get_table_dydb_object(db_resource, "PREPROCESS")
                filename_preprocess = f"preprocessed_{request['filename']}"
                table.delete_item(Key={
                    'project_id': project_id,
                    'filename': filename_preprocess
                })
                
            # update information in prj summary all (count, total_size)
            dydb_update_prj_sum(table_sum_all, project_id, key, value['count'], value['ts'])
            
        # update the thumnail key if it exists in the deleted images
        # get thumnail filename
        response = table_sum_all.get_item(
                                    Key = {
                                        'project_id': project_id,
                                        'type': 'ORIGINAL'
                                    }
                                )
        print('response get sum_all: ', response)
        if response.get('Item'):
            thum_name = response['Item'].get('thu_name', None)
            if thum_name:
                # check this filename still exist in data original

                table_ori = db_resource.Table(os.environ['T_DATA_ORI'])
                response = table_ori.get_item(
                                Key = {
                                    'project_id': project_id,
                                    'filename': thum_name
                                }
                            )
                
                print('response get item ori: ', response)
                if response.get('Item', None) is None:
                    #--- not exist, it means image was deleted, so choose another thumnail
                    # get ls_data in original
                    response = table_ori.query(
                                            KeyConditionExpression=Key('project_id').eq(project_id),
                                        )
                    print('response query item ori: ', response)
                    if len(response['Items']) == 0:
                        thum_key_r = None
                        thum_name_r = None
                    else:
                        thum_key_r = response['Items'][0]['s3_key']
                        thum_name_r = response['Items'][0]['filename']
                        
                    # update to summary_all
                    response = table_sum_all.update_item(
                                        Key={
                                            'project_id': project_id,
                                            'type': 'ORIGINAL',
                                        },
                                        ExpressionAttributeNames = {
                                            '#TK': 'thu_key',
                                            '#TN': 'thu_name'
                                        },
                                        ExpressionAttributeValues = {
                                            ':tk': thum_key_r,
                                            ':tn': thum_name_r
                                        },
                                        UpdateExpression='SET #TK = :tk, #TN = :tn' 
                                    )
                    print('update ok')
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True, 
                "success": False, 
                "message": repr(e), 
                "data": None})
    
    return convert_response({'data': {}, 
            "error": False, 
            "success": True, 
            "message": None})