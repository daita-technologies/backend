import json
import boto3
import hashlib
import hmac
import base64
import os

from boto3.dynamodb.conditions import Key, Attr
from config import *
from response import *
from error_messages import *
from identity_check import *
from utils import *
MAX_NUMBER_ITEM_DELETE = 100


def delete_image_healthycheck_info(db_resource,project_id,healthcheck_id):
    table_healthycheck_info = db_resource.Table(os.environ['TABLE_HEALTHCHECK_INFO'])
    table_healthycheck_info.delete_item(
                                Key = {
                                    'project_id': project_id,
                                    'healthcheck_id': healthcheck_id
                                }
                            )    
def delete_reference_images(db_resource,identity_id,project_id,deletedfilename):
    print(f'Log Debug: {deletedfilename}')
    table_project = db_resource.Table(os.environ['TABLE_PROJECT'])
    queryResponse = table_project.query(
        KeyConditionExpression=Key('identity_id').eq(identity_id),
        FilterExpression=Attr('project_id').eq(project_id)
    )
    with table_project.batch_writer() as batch:
        for each in queryResponse['Items']:
            reference_images = each['reference_images']
            new_reference_image = {}
            for k , v in reference_images.items():
                if not deletedfilename in v :
                    new_reference_image[k] = v
            
            resp = table_project.update_item(
                                    Key={
                                        'project_name': each['project_name'],
                                        'identity_id': identity_id ,
                                    },
                                    ExpressionAttributeNames= {
                                        '#r': 'reference_images',
                                    },
                                    ExpressionAttributeValues = {
                                        ':r':  new_reference_image
                                    },
                                    UpdateExpression = 'SET #r = :r' 
                                )
            print(resp)
            
    
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
        return  generate_response(
            message=str(e),
            status_code=HTTPStatus.OK,
            data={ },
            error= False
        )    

    # update data to DB 
    # we use batch_write, it means that if key are existed in tables => overwrite
    db_resource = boto3.resource('dynamodb')
    try:
        table_sum_all = db_resource.Table(os.environ['TABLE_PROJECT_SUMMARY'])

        for key, value in dict_request.items():
            
            project_id = value['project_id']
            
            # delete in data table
            table = get_table_dydb_object(db_resource, key)
            for request in value['ls_rq']:
                item = table.get_item(Key={
                    'project_id': project_id,
                    'filename': request['filename']
                })
                try:
                    delete_reference_images(db_resource=db_resource,identity_id=identity_id,project_id=project_id,deletedfilename=request['filename'])
                except Exception as e:
                    print(e)
                if ('healthcheck_id' in item['Item']) and (not item['Item']['healthcheck_id'] is None or  isinstance(item['Item']['healthcheck_id'],str)):
                    delete_image_healthycheck_info(db_resource=db_resource,project_id=project_id,healthcheck_id=item['Item']['healthcheck_id'])
                
                table.delete_item(Key={
                    'project_id': project_id,
                    'filename': request['filename']
                })
                # check reference image 


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
        return generate_response(
            message=str(e),
            status_code=HTTPStatus.OK,
            data={ },
            error= True
        )    
    
    return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={ },
        )    