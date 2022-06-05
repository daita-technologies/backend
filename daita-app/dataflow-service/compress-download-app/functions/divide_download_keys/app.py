import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
import json
from utils import get_bucket_key_from_s3_uri, split_ls_into_batch


CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 8))
db_resource = boto3.resource("dynamodb")
data_original_table = db_resource.Table(os.getenv("TableDataOriginal"))
data_augment_table = db_resource.Table(os.getenv("TableDataAugment"))
data_preprocess_table = db_resource.Table(os.getenv("TableDataPreprocess"))
s3 = boto3.client('s3')


def lambda_handler(event, context):
    print(event)
    down_type: str = event["down_type"]   # ALL, augment, preprocess, original
    project_name: str = event["project_name"]
    project_id: str = event["project_id"]
    task_id: str = event["task_id"]
    identity_id: str = event["identity_id"]

    # get list key of the project
    ls_table = []
    if down_type == "ALL":
        ls_table.append(data_original_table)
        ls_table.append(data_augment_table)
        ls_table.append(data_preprocess_table)
    elif down_type == "ORIGINAL":
        ls_table.append(data_original_table)
    elif down_type == "PREPROCESS":
        ls_table.append(data_preprocess_table)
    elif down_type == "AUGMENT":
        ls_table.append(data_augment_table)
    else:
        raise Exception(f"invalid down_type: {down_type}")

    ## get all dowloaded object information from DB
    ls_object = []
    for table in ls_table:
        response = table.query(
                KeyConditionExpression = Key('project_id').eq(project_id),
                ProjectionExpression='filename, s3_key, classtype, gen_id, type_method',
                Limit = 500
            )
        ls_object = ls_object + response['Items']
        # print("total len response: ", len(response['Items']))
        next_token = response.get('LastEvaluatedKey', None)
        while next_token is not None:
            response = table.query(
                KeyConditionExpression = Key('project_id').eq(project_id),
                ProjectionExpression='filename, s3_key, classtype, gen_id, type_method',
                Limit = 500,
                ExclusiveStartKey=next_token,
            )
            next_token = response.get('LastEvaluatedKey', None)
            # print("total len response next: ", len(response['Items']))
            ls_object = ls_object + response['Items']

    if len(ls_object) == 0:
        return {"s3_key": None}
    print("Final len: ", len(ls_object))

    file_chunks = []
    for size in range(0, len(ls_object), CHUNK_SIZE):
        file_chunks.append(ls_object[size:size + CHUNK_SIZE])
        
    if len(ls_object)>0:
        bucket, folder = get_bucket_key_from_s3_uri(ls_object[0]["s3_key"])
        folder = "/".join(folder.split("/")[:-1])
        s3_key_path = os.path.join(folder, f"download_state_json/{task_id}/download_devide.json")
        s3.put_object(
                Body=json.dumps(file_chunks),
                Bucket= bucket,
                Key= s3_key_path
            )            
    else:
        bucket = None
        s3_key_path = None

    return {
        "file_chunks": list(range(len(file_chunks))),
        "bucket": bucket,
        "s3_key_path": s3_key_path,
        "workdir": task_id,
    }
