from datetime import datetime
import uuid
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
import re

def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()

def create_unique_id():
    return str(uuid.uuid4())

def create_task_id_w_created_time():
    return f"{convert_current_date_to_iso8601()}-{create_unique_id()}"

def from_dynamodb_to_json(item):
    d = TypeDeserializer()
    return {k: d.deserialize(value=v) for k, v in item.items()}

def get_bucket_key_from_s3_uri(uri: str):
    if not 's3' in uri[:2]:
        temp = uri.split('/')
        bucket = temp[0]
        filename = '/'.join([temp[i] for i in range(1,len(temp))])
    else:
        match =  re.match(r's3:\/\/(.+?)\/(.+)', uri)
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
        if len(ls_batch_current)==batch_size:
            ls_batch.append(ls_batch_current)
            ls_batch_current = []
        ls_batch_current.append(info)
    if len(ls_batch_current)>0:
        ls_batch.append(ls_batch_current)
    
    return ls_batch
