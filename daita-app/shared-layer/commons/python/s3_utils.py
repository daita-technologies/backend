import re
import os
import boto3

## this file contain common functions for S3 action
s3 = boto3.client('s3')

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
def download(uri,folder):
    bucket, filename =  split(uri)
    basename = os.path.basename(filename)
    new_image = os.path.join(folder,basename)
    s3.download_file(bucket,filename,new_image)