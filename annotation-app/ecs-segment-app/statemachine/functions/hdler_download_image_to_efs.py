import boto3
import re
import os
import json

from response import *

from lambda_base_class import LambdaBaseClass
s3 = boto3.client('s3')

def save_image_to_efs(s3_key,folder=os.environ['EFSPATH']):
    print(s3_key)
    bucket, filename = split(s3_key)
    basename = os.path.basename(filename)
    new_image = os.path.join(folder,basename)
    s3.download_file(bucket,filename,new_image)
    
    return ''

def parse_json_ecs_segmentation(records):
    newJson = {'images':[]}
    
    for id ,record in enumerate(records):
        os.makedirs(os.path.join(os.environ['EFSPATH'],record['project_id']),exist_ok=True)
        newJson['images'].append(
                {
                    "image_path":os.path.join('/app/data',save_image_to_efs('s3://{}'.format(record['s3_key']))),
                    "image_id": id
                },
        )
    
    fileinput = os.path.join(os.environ['EFSPATH'],'input.json')
    with open(fileinput,'w') as f:
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
        print(event)
        print(os.listdir(os.environ['EFSPATH']))
        # input = '/app/data'  + 
        input = '/app/data/input.json' ## test efs
        print(os.listdir(os.environ['EFSPATH']))
        print(input)
        return {
                "Name": os.environ['CONTAINER_NAME'],
                "Command": ["--input_json_path",input,"--output_folder","/app/data"]
        }

@error_response
def lambda_handler(event, context):
    return DownloadImageEFSClass().handle(event=event,context=context)