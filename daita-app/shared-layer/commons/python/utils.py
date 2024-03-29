from datetime import datetime
from decimal import Decimal
import uuid
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
from boto3.dynamodb.conditions import Key, Attr
import re
import boto3
import os
import json

def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()


def create_unique_id():
    """
    Create an unique id 
    """
    return str(uuid.uuid4())



def create_task_id_w_created_time():
    """
    Create unique id combine with current day for task_id of all task table
    """
    return f"{convert_current_date_to_iso8601()}-{create_unique_id()}"


def from_dynamodb_to_json(item):
    # print(f"Item to serialize: \n {item}")
    d = TypeDeserializer()
    serialize = {k: d.deserialize(value=v) for k, v in item.items()}

    for key, value in serialize.items():
        if type(value) is Decimal:
            serialize[key] = int(value)

    # print(f"Result after serialize: \n {serialize}")
    return serialize


def get_bucket_key_from_s3_uri(uri: str):
    if not 's3' in uri[:2]:
        temp = uri.split('/')
        bucket = temp[0]
        filename = '/'.join([temp[i] for i in range(1, len(temp))])
    else:
        match = re.match(r's3:\/\/(.+?)\/(.+)', uri)
        bucket = match.group(1)
        filename = match.group(2)
    return bucket, filename


def split_ls_into_batch(ls_info, batch_size=8):
    """
    split the element in list into a batch with the batch size
    """
    ls_batch = []
    ls_batch_current = []
    for info in ls_info:
        if len(ls_batch_current) == batch_size:
            ls_batch.append(ls_batch_current)
            ls_batch_current = []
        ls_batch_current.append(info)
    if len(ls_batch_current) > 0:
        ls_batch.append(ls_batch_current)

    return ls_batch


def get_data_table_name(type_method):
    if type_method == 'ORIGINAL':
        return 'data_original'
    elif type_method == 'AUGMENT':
        return 'data_augment'
    elif type_method == 'PREPROCESS':
        return 'data_preprocess'
    else:
        raise Exception(f'Method {type_method} is not exist!')

def get_num_prj(identity_id):
    db_resource = boto3.resource("dynamodb")
    table = db_resource.Table(os.environ['TABLE_PROJECT'])
    response = table.query(
            KeyConditionExpression=Key('identity_id').eq(identity_id),
            Select = 'COUNT'
        )
    return response.get("Count", 0)
def get_table_dydb_object(db_resource, type_method):
    table_name = get_data_table_name(type_method)
    return db_resource.Table(table_name)

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
def dydb_update_prj_sum(table, project_id, type_method, count_add, size_add):
    response = table.update_item(
        Key={
            'project_id': project_id,
            'type': type_method,
        },
        ExpressionAttributeNames={
            '#CO': 'count',
            '#TS': 'total_size'
        },
        ExpressionAttributeValues={
            ':ts': -size_add,
            ':co': -count_add
        },
        UpdateExpression='ADD #TS :ts, #CO :co'
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
            Item=new_item
        )

        # delete item in table project
        table.delete_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            }
        )


def aws_get_identity_id(id_token, USER_POOL_ID, IDENTITY_POOL_ID):
    identity_client = boto3.client('cognito-identity')
    PROVIDER = f'cognito-idp.{identity_client.meta.region_name}.amazonaws.com/{USER_POOL_ID}'

    try:
        identity_response = identity_client.get_id(
            IdentityPoolId=IDENTITY_POOL_ID,
            Logins={PROVIDER: id_token})
    except Exception as e:
        print('Error: ', repr(e))
        raise

    identity_id = identity_response['IdentityId']

    return identity_id

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