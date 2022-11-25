import boto3
import re
import os
import json

from response import *

from lambda_base_class import LambdaBaseClass

table = boto3.client('dynamodb')
s3 = boto3.client('s3')

def update_s3_gen(project_id, filename, s3_key_gen):
    response = table.update_item(
                TableName=os.environ["TABLE"],
                Key={
                    'project_id': {
                        'S': project_id
                    },
                    'filename': {
                        'S': filename
                    }
                },
                ExpressionAttributeNames={
                  '#gen': 's3_key_segm',
                },
                ExpressionAttributeValues={
                  ':gen':{
                    'S': s3_key_gen
                  }
                },
                UpdateExpression='SET #gen = :gen',
            )
    print(f'Response ',response)

def upload_segmentation_s3(data,s3_key):
    dirfilename =  os.path.dirname(s3_key)
    dirfilename = dirfilename.replace('raw_data','clone_project')
    basename =  os.path.splitext(os.path.basename(s3_key))[0] + '_segment.json'
    filename = os.path.join(dirfilename, basename)
    bucket =  filename.split('/')[0]
    key = '/'.join(filename.split('/')[1:])
    s3.put_object(
                    Body=data,
                    Bucket=bucket ,
                    Key= key
                )
    return filename

@error_response
def lambda_handler(event, context):
    output_folder = os.path.join(event['input_folder'],'output')
    output_folder = os.path.join(os.environ['EFSPATH'],output_folder)
    
    for index , it in enumerate(event['records']):
        with open(os.path.join(output_folder,str(index)+'.json'),'r') as f:
            # data = json.load(f)
            s3_key = upload_segmentation_s3(f.read(),s3_key=it['s3_key'])
            update_s3_gen(it['project_id'], it['filename'],s3_key)
    return {}