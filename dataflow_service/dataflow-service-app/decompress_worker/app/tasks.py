import os
import tempfile

from kombu.utils.url import safequote
from celery import Celery
import boto3


s3 = boto3.client('s3')
BUCKET_NAME = ""


AWS_REGION = os.getenv("AWS_REGION")
AWS_ACCESS_KEY_ID = safequote(os.getenv("AWS_ACCESS_KEY_ID"))
AWS_SECRET_ACCESS_KEY = safequote(os.getenv("AWS_SECRET_ACCESS_KEY"))
DECOMPRESS_FILE_QUEUE_URL = os.getenv("DECOMPRESS_FILE_QUEUE_URL")
EFS_COMPRESSFILE_MOUNT_POINT = os.getenv("EFS_COMPRESSFILE_MOUNT_POINT")


broker_url = f"sqs://{AWS_ACCESS_KEY_ID}:{AWS_SECRET_ACCESS_KEY}@"
app = Celery("tasks", broker=broker_url)
app.conf.update({
        "broker_transport_options": {
            "region": AWS_REGION,
            "predefined_queues": {
                "decompress-file": {
                    "url": DECOMPRESS_FILE_QUEUE_URL,
                    "access_key_id": AWS_ACCESS_KEY_ID,
                    "secret_access_key": AWS_SECRET_ACCESS_KEY,
                }
            }
        }
    })


@app.task
def decompress_file(file_url):
   with tempfile.TemporaryFile(dir=EFS_COMPRESSFILE_MOUNT_POINT) as compressed:
       s3.download_fileobj(BUCKET_NAME, file_url, data)

    # unzip file

    # upload decompressed file to s3

    # send decompress file to project_upload_update.py