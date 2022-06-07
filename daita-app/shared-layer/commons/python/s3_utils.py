import re
import os
from urllib import response
import boto3
from botocore.client import Config

## this file contain common functions for S3 action
s3 = boto3.client("s3")
s3_conf = boto3.client("s3", config=Config(signature_version="s3v4"))


def split(uri):
    if not "s3" in uri[:2]:
        temp = uri.split("/")
        bucket = temp[0]
        filename = "/".join([temp[i] for i in range(1, len(temp))])
    else:
        match = re.match(r"s3:\/\/(.+?)\/(.+)", uri)
        bucket = match.group(1)
        filename = match.group(2)
    return bucket, filename


def download(uri, folder):
    bucket, filename = split(uri)
    basename = os.path.basename(filename)
    new_image = os.path.join(folder, basename)
    s3.download_file(bucket, filename, new_image)


def generate_presigned_url(s3_link, expired=3600, bucket=None, object_key=None):

    if s3_link is not None:
        bucket, object_key = split(s3_link)

    reponse = s3_conf.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": bucket, "Key": object_key},
        ExpiresIn=1 * 60 * 60,
    )

    return reponse
