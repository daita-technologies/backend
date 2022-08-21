import os
import re
import cv2
import boto3
import threading
import numpy as np
from Queue import Queue
from error_messages import *
from response import *
from config import *
from lambda_base_class import LambdaBaseClass
from itertools import chain, islice


def batcher(iterable, size):
    iterator = iter(iterable)
    for first in iterator:
        yield list(chain([first], islice(iterator, size - 1)))


class ResizeImageCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.images = body['images']
        self.data_type = body['data_type']
        self.project_id = body['project_id']
        self.s3 = boto3.client('s3')
        self.table = boto3.resource('dynamodb').Table(body['resource_type'])

    def split(self, uri):
        if not 's3' in uri[:2]:
            temp = uri.split('/')
            bucket = temp[0]
            filename = '/'.join([temp[i] for i in range(1, len(temp))])
        else:
            match = re.match(r's3:\/\/(.+?)\/(.+)', uri)
            bucket = match.group(1)
            filename = match.group(2)
        return bucket, filename

    def get_image_from_s3(self, url):
        bucket, filename = self.split(url)
        resultS3 = self.s3.get_object(Bucket=bucket, Key=filename)
        image = np.asarray(bytearray(resultS3.read()), dtype="uint8")
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
        return image

    def upload_s3(self, image, ext, bucket, filename):
        _, encoded_image = cv2.imencode(ext, image)
        bytearr = encoded_image.tobytes()
        self.s3.put_object(Bucket=bucket, Key=filename, Body=bytearr)
        s3_key = f's3://{bucket}/{filename}'
        return s3_key

    def update_thumbnail(self, filename, thumbnail):
        response = self.table.update_item(
            Key={
                'project_id': self.project_id,
                'filename': filename,
            },
            ExpressionAttributeNames={
                '#thumbnail' 'thumbnail',
            },
            ExpressionAttributeValues={
                ':thumbnail':  thumbnail,
            },
            UpdateExpression='SET #thumbnail = :thumbnail'
        )

    def resize_image(self, queue):
        while True:
            s3_url = queue.get()
            basefilename = os.path.basename(s3_url)
            ext = os.path.splitext(os.path.basename(s3_url))[-1]
            image = self.get_image_from_s3(s3_url)
            image = cv2.resize(image, (720, 1280))
            s3_key_thumbnail = self.upload_s3(image=image, ext=ext)
            self.update_thumbnail(basefilename, s3_key_thumbnail)
            queue.task_done()

    def handle(self, event, context):
        self.parser(event)
        enclosure_queue = Queue()
        for _ in range(10):
            worker = threading.Thread(
                target=self.resize_image, args=(enclosure_queue,))
            worker.daemon = True
            worker.start()
        for s3_url in self.images:
            enclosure_queue.put(s3_url)

        enclosure_queue.join()


@error_response
def lambda_handler(event, context):
    return ResizeImageCls().hande(event, context)
