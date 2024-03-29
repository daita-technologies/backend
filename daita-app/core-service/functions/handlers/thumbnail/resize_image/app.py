import os
import re
import boto3
import PIL
import threading
from queue import Queue
from error_messages import *
from response import *
from config import *
from PIL import Image
from io import BytesIO
from lambda_base_class import LambdaBaseClass
from thumbnail import Thumbnail


class DynamoDBNewImageUpdated(object):
    def __init__(self,info) -> None:
        self.project_ID = info['project_id']
        self.filename = info['filename']
        self.thumbnail = None
        self.s3_url = info['s3_urls']
        self.table_name  = info['table']

class ResizeImageCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.s3 = boto3.client('s3')
        self.table = boto3.resource('dynamodb')

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
        obj_body = self.s3.get_object(Bucket=bucket, Key=filename)
        img = Image.open(BytesIO(obj_body["Body"].read()))
        img = img.resize((int(img.size[1]*0.4),int(img.size[0]*0.4)), PIL.Image.ANTIALIAS)
        buffer = BytesIO()
        img.convert('RGB').save(buffer, 'JPEG')
        buffer.seek(0)
        return buffer

    def upload_s3(self, image, ext, bucket, filename):
        self.s3.put_object(Bucket=bucket, Key=filename, Body=image)
        s3_key = f's3://{bucket}/{filename}'
        return s3_key

    def update_thumbnail(self, item : DynamoDBNewImageUpdated):
        response = self.table.Table(item.table_name).update_item(
            Key={
                'project_id': item.project_ID,
                'filename': item.filename,
            },
            ExpressionAttributeNames={
                '#thumbnail': 'thumbnail',
            },
            ExpressionAttributeValues={
                ':thumbnail':  item.thumbnail,
            },
            UpdateExpression='SET #thumbnail = :thumbnail'
        )
        print(f'Response : {response}')

    def resize_image(self, queue):
        while True:
            item = queue.get()
            try:
                ext = os.path.splitext(os.path.basename(item.s3_url))[-1]
                image = self.get_image_from_s3(item.s3_url)
                bucket, filename = self.split(item.s3_url)
                filenameSlice =  filename.split('/')
                filenameSlice.insert(len(filenameSlice)-1,'thumbnail')
                newfilename = '/'.join(filenameSlice)
                item.thumbnail=  self.upload_s3(image=image, ext=ext,bucket=bucket,filename=newfilename)
            except Exception as e:
                print(f'ERROR :{e}')
                queue.task_done()
                return
            # print(f'Logs Check {item.thumbnail}')
            self.update_thumbnail(item)
            queue.task_done()

    def handle(self, event, context):
        print(f'Log Debug {event}')
        listRecord = []
        for it in event:
            listRecord.append(Thumbnail(it))
        enclosure_queue = Queue()
        for _ in range(5):
            worker = threading.Thread(
                target=self.resize_image, args=(enclosure_queue,))
            worker.daemon = True
            worker.start()
        for item in listRecord:
            enclosure_queue.put(item)
        enclosure_queue.join()
        return {"message": "Trigger Successfully"}


@error_response
def lambda_handler(event, context):
    return ResizeImageCls().handle(event, context)
