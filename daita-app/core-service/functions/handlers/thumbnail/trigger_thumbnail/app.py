import os
import json
import boto3
from error_messages import *
from response import *
from config import *
from lambda_base_class import LambdaBaseClass

class CreateThumbnailCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.client_events = boto3.client('events')    

    def handle(self,event,context):
        records =  event['Records']
        listRecord = []
        print(f'logs :{records}')
        for record in records:
            if record['eventName'] == 'INSERT':
                tempItem =  {
                    'project_id': record['dynamodb']['Keys']['project_id']['S'],
                    'filename' : record['dynamodb']['Keys']['filename']['S'],
                    'table': record['eventSourceARN'].split(':')[5].split('/')[1],
                    's3_urls':record['dynamodb']['NewImage']['s3_key']['S']
                }
                listRecord.append(tempItem)
        print(listRecord)
        if len(listRecord) == 0 :
            print("Nothing image need to create thumbnail")
            return  {"message":"ok"}
        response = self.client_events.put_events(
                        Entries=[
                            {
                                'Source': 'source.events',
                                'DetailType': 'lambda.event',
                                'Detail': json.dumps({'body':listRecord}),
                                'EventBusName': os.environ["EVENT_BUS_NAME"]
                            },
                        ]
                    )
        print(f'Log: {response}')
        return {"message":"ok"}


@error_response
def lambda_handler(event, context):
    return CreateThumbnailCls().handle(event=event,context=context)