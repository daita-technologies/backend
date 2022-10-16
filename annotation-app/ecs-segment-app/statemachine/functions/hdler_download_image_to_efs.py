import boto3
import re
import os
import json

from response import *

from lambda_base_class import LambdaBaseClass
s3 = boto3.client('s3')
def save_image_to_efs(s3_key : str,folder : str):
    print(s3_key)
    bucket, filename = split(s3_key)
    basename = os.path.join(folder,os.path.basename(filename))
    new_image = os.path.join(str(os.environ['EFSPATH']),basename)
    s3.download_file(bucket,filename,new_image)
    
    return basename

def parse_json_ecs_segmentation(records,input_folder):
    newJson = {'images':[]}
    
    for id ,record in enumerate(records):
        newJson['images'].append(
                {
                    "image_path":os.path.join(str(os.environ['CONTAINER_MOUNT']),save_image_to_efs('s3://{}'.format(record['s3_key']),input_folder)),
                    "image_id": id
                },
        )
    
    fileinput = os.path.join(input_folder,'input.json')
    with open(os.path.join(str(os.environ['EFSPATH']), fileinput),'w') as f:
        json.dump(newJson,f)
    return fileinput

def split(uri):
    if not 's3' in uri[:2]:
        temp = uri.split('/')
        bucket = temp[0]
        filename = '/'.join([temp[i] for i in range(1,len(temp))])
    else:
        match =  re.match(r's3:\/\/(.+?)\/(.+)', uri)
        bucket = match.group(1)
        filename = match.group(2)
    return bucket, filename 

class DownloadImageEFSClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def handle(self,event, context):
        input_folder = event['input_folder']
        os.makedirs(os.path.join(str(os.environ['EFSPATH']),input_folder),exist_ok=True)
        inputJson = parse_json_ecs_segmentation(event['records'],input_folder)
        inputJsonContainerVolume = os.path.join(str(os.environ['CONTAINER_MOUNT']),inputJson)
        output_folder = os.path.join(input_folder,'output')
        os.makedirs(os.path.join(str(os.environ['EFSPATH']),output_folder),exist_ok=True)
        return {
                "Name": os.environ['CONTAINER_NAME'],
                "Command": ["--input_json_path",inputJsonContainerVolume,"--output_folder",os.path.join(str(os.environ['CONTAINER_MOUNT']),output_folder)]
        }

@error_response
def lambda_handler(event, context):
    return DownloadImageEFSClass().handle(event=event,context=context)