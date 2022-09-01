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
        img = img.resize((720,1280), PIL.Image.ANTIALIAS)
        buffer = BytesIO()
        img.convert('RGB').save(buffer, 'JPEG')
        print("Test IMAGEEE")
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
                '#thumbnail' 'thumbnail',
            },
            ExpressionAttributeValues={
                ':thumbnail':  item.thumbnail,
            },
            UpdateExpression='SET #thumbnail = :thumbnail'
        )
        print(response)

    def resize_image(self, queue):
        while True:
            item = queue.get()
            print(f'Logs Debug Queue: {item.s3_url}')
            try:
                ext = os.path.splitext(os.path.basename(item.s3_url))[-1]
                print(f'{ext}')
                image = self.get_image_from_s3(item.s3_url)
                print("DEBUGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG")
                bucket, filename = self.split(item.s3_url)
                print(filename)
                filenameSlice =  filename.split('/')
                filenameSlice = filenameSlice.insert(len(filenameSlice)-1,'thumbnail')
                print(filenameSlice)
                newfilename = '/'.join(filenameSlice)
                print(f'log new filename {newfilename}')
                item.thumbnail=  self.upload_s3(image=image, ext=ext,bucket=bucket,filename=newfilename)
            except Exception as e:
                print(f'ERROR :{e}')
                pass
            print(f'Logs Check {item.thumbnail}')
            self.update_thumbnail(item)
            queue.task_done()

    def handle(self, event, context):
        records =  event['Records']
        listRecord = []
        print(f'logs :{records}')
        for record in records:
            print(f'Logs Debug : {record}')
            # if record['NewImage']
            tempItem =  DynamoDBNewImageUpdated({
                'project_id': record['dynamodb']['Keys']['project_id']['S'],
                'filename' : record['dynamodb']['Keys']['filename']['S'],
                'table': record['eventSourceARN'].split(':')[5].split('/')[1],
                's3_urls':record['dynamodb']['NewImage']['s3_key']['S']
            })
            print(tempItem.s3_url)
            listRecord.append(tempItem)
        
        # self.parser(event)
        enclosure_queue = Queue()
        for _ in range(10):
            worker = threading.Thread(
                target=self.resize_image, args=(enclosure_queue,))
            worker.daemon = True
            worker.start()
        print(listRecord)
        for item in listRecord:
            enclosure_queue.put(item)
        enclosure_queue.join()
        return {"message": "Trigger Successfully"}


@error_response
def lambda_handler(event, context):
    return ResizeImageCls().handle(event, context)
