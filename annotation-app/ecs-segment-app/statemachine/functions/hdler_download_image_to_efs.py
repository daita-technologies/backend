import boto3
import re
import os

from response import *

from lambda_base_class import LambdaBaseClass

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
        return {
                "Name": os.environ['CONTAINER_NAME'],
                "Command": ["--input_json_path","data/sample/input.json","--output_folder","data/sample/output"]
        }

@error_response
def lambda_handler(event, context):
    return DownloadImageEFSClass().handle(event=event,context=context)