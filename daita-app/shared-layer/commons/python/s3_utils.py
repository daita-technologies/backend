import re
import os
from urllib import response
import boto3
from botocore.client import Config

## this file contain common functions for S3 action
s3 = boto3.client('s3')
s3_conf = boto3.client('s3', config=Config(signature_version='s3v4'))

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

def generate_presigned_url(s3_link, expired=3600, bucket = None, object_key = None):

    if s3_link is not None:
        bucket, object_key = split(s3_link)

    reponse = s3_conf.generate_presigned_url(
        ClientMethod='get_object',
        Params={
            'Bucket': bucket,
            'Key': object_key
        },
        ExpiresIn=1*60*60        
    )
    
    return reponse

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

def separate_s3_uri(s3_uri, bucket_name):
    """
    split the bucket_name and the key of file from s3 uri
    EXP:
    client-data-test/us-east-2:1d66c2cf-28c7-4222-b517-73c78c83f132/jhgjhgj_a95bac00047140429e027876861b7bcd, bucket_name = client-data-test
        -> output: ["client-data-test", "us-east-2:1d66c2cf-28c7-4222-b517-73c78c83f132/jhgjhgj_a95bac00047140429e027876861b7bcd"]
    s3://client-data-test/us-east-2:1d66c2cf-28c7-4222-b517-73c78c83f132/jhgjhgj_a95bac00047140429e027876861b7bcd, bucket_name = client-data-test
        -> output: ["client-data-test", "us-east-2:1d66c2cf-28c7-4222-b517-73c78c83f132/jhgjhgj_a95bac00047140429e027876861b7bcd"]
    """
    if not 's3://' in s3_uri[:2]:
        temp = s3_uri.split('/')
        
    else:
        s3_uri = s3_uri.replace("s3://", "")
        temp = s3_uri.split('/')
    
    bucket = temp[0]
    filename = '/'.join(temp[1:])
    
    return bucket, filename 