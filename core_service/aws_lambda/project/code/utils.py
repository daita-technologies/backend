import json
import hashlib
import base64
from datetime import datetime
import boto3
import os
from boto3.dynamodb.conditions import Key, Attr


def convert_response(data):
    if data.get('message', None):
        # print("convert: ",data['message'])
        # print("type: ", type(data['message']))
        data['message'] = data['message'].replace("Exception('", "").replace("')", "")
    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        "body": json.dumps(data),
    }

def get_num_prj(identity_id):
    db_resource = boto3.resource("dynamodb")
    table = db_resource.Table(os.environ['T_PROJECT'])
    response = table.query(
            KeyConditionExpression=Key('identity_id').eq(identity_id),
            Select = 'COUNT'
        )
    return response.get("Count", 0)

def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()

def aws_get_identity_id(id_token):
    identity_client = boto3.client('cognito-identity')
    PROVIDER = f'cognito-idp.{identity_client.meta.region_name}.amazonaws.com/{os.environ["USER_POOL_ID"]}'

    try:
        identity_response = identity_client.get_id(
                              IdentityPoolId=os.environ['IDENTITY_POOL_ID'],
                              Logins = {PROVIDER: id_token})
    except Exception as e:
        print('Error: ', repr(e))
        raise

    identity_id = identity_response['IdentityId']

    return identity_id

def dydb_get_project_id(table, identity_id, project_name):
    try:
        response = table.get_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ProjectionExpression= 'project_id'
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise
    if response.get('Item', None):
        return response['Item']['project_id']
    return None

def dydb_get_project(db_resource, identity_id, project_name):
    try:
        table = db_resource.Table(os.environ['T_PROJECT'])
        response = table.get_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ProjectionExpression= 'project_id, s3_prefix, times_generated, times_propr'
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise
    if response.get('Item', None):
        return response['Item']
    return None

def dydb_get_project_full(table, identity_id, project_name):
    try:
        response = table.get_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise
    if response.get('Item', None):
        return response['Item']
    return None

def dydb_update_project_data_type_number(db_resource, identity_id, project_name, data_type, data_number, times_generated):
    try:
        table = db_resource.Table(os.environ['T_PROJECT'])
        response = table.update_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ExpressionAttributeNames= {
                '#DA_TY': data_type
            },
            ExpressionAttributeValues = {
                ':va':  data_number,
                ':da': convert_current_date_to_iso8601(),
                ':tg': times_generated
            },
            UpdateExpression = 'SET #DA_TY = :va , updated_date = :da, times_generated = :tg'
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise
    if response.get('Item', None):
        return response['Item']
    return None


def dydb_get_task_progress(table, identity_id, task_id):
    try:
        response = table.get_item(
            Key={
                'identity_id': identity_id,
                'task_id': task_id,
            }
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise
    if response.get('Item', None):
        return response['Item']

    raise(Exception('Task ID does not exist'))

def dydb_update_prj_sum(table, project_id, type_method, count_add, size_add):
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
                ':ts':  -size_add,
                ':co': -count_add
            },
            UpdateExpression = 'ADD #TS :ts, #CO :co'
        )

def dydb_update_delete_project(table, table_project_delete, identity_id, project_name):
    # get current project
    response = table.get_item(Key={
                'identity_id': identity_id,
                'project_name': project_name,
            })

    if response.get('Item'):
        new_item = response['Item']
        new_item['delete_date'] = convert_current_date_to_iso8601()

        # create new item in table project delete
        table_project_delete.put_item(
                Item = new_item
            )

        # delete item in table project
        table.delete_item(
                Key = {
                    'identity_id': identity_id,
                    'project_name': project_name,
                }
            )

def dydb_update_class_data(table, project_id, filename, classtype):
    response = table.update_item(
            Key={
                'project_id': project_id,
                'filename': filename,
            },
            ExpressionAttributeNames= {
                '#CT': 'classtype',
            },
            ExpressionAttributeValues = {
                ':ct':  classtype,

            },
            UpdateExpression = 'SET #CT = :ct'
        )


def move_data_s3(source, target, bucket_name):
    ls_info = []
    #list all data in s3
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)

    for obj in bucket.objects.filter(Prefix=source):
        if obj.key.endswith('/'):
            continue

        old_source = { 'Bucket': bucket_name,
                       'Key': obj.key}
        # replace the prefix
        new_prefix = target.replace(f"{bucket_name}/", "")
        new_key = f'{new_prefix}/{obj.key.replace(source, "")}'
        s3.meta.client.copy(old_source, bucket_name, new_key)

        ls_info.append((new_key.split('/')[-1], f"{bucket_name}/{new_key}", obj.size))

    return ls_info

def create_single_put_request(dict_value):
    dict_re = {
        'PutRequest': {
            'Item': {
            }
        }
    }
    for key, value in dict_value.items():
        dict_re['PutRequest']['Item'][key] = {
            value[0]: value[1]
        }
    return dict_re

def get_data_table_name(type_method):
    if type_method == 'ORIGINAL':
        return os.environ["T_DATA_ORI"]
    elif type_method == 'AUGMENT':
        return os.environ["T_DATA_AUGMENT"]
    elif type_method == 'PREPROCESS':
        return os.environ["T_DATA_PREPROCESS"]
    else:
        raise Exception(f'Method {type_method} is not exist!')

def get_table_dydb_object(db_resource, type_method):
    table_name = get_data_table_name(type_method)
    return db_resource.Table(table_name)


def create_secret_hash(
        clientSecret: str,
        user: str,
        clientPoolID: str
    ) -> str:
    hash = hashlib.sha256()
    hash.update(clientSecret)
    hash.update(user + clientPoolID)
    return base64.b64encode(hash.digest().encode('ascii'))
