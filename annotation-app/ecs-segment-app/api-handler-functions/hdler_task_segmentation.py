import boto3
import re
import os
import json
import glob

from response import *

from lambda_base_class import LambdaBaseClass



class EventTaskQueueSegmentationClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.s3 = boto3.client('s3')
        dns = (os.environ['SQS_VPC_ENDPOINT']).split(":")[1]
        self.sqs = boto3.client('sqs',endpoint_url='https://{}'.format(dns))
        self.sqsResourse = boto3.resource('sqs',endpoint_url='https://{}'.format(dns))
    
    def handle(self,event,context):
        for record in event['Records']:
            body = json.loads(record['body'])
            print(body)
            OutDir =  glob.glob(os.path.join(os.environ['EFSPATH'],body['output_directory'])+'/*')
            if len(OutDir) == len(body['output_directory']):
                self.sqs.delete_message(
                    QueueUrl=os.environ['QUEUE'],
                    ReceiptHandle= record['receiptHandle']
                )
            else:
                nbReplay = 0
                if 'sqs-dlq-replay-nb' in record['messageAttributes']:
                     nbReplay = int(record['messageAttributes']['sqs-dlq-replay-nb']["stringValue"])
                nbReplay += 1
                if nbReplay > 40:
                    continue
                attributes = record['messageAttributes']
                attributes.update({'sqs-dlq-replay-nb': {'StringValue': str(nbReplay), 'DataType': 'Number'}})
                _sqs_attributes_cleaner(attributes)
                self.sqs.send_message(
                    QueueUrl=os.environ['QUEUE_URL'],
                    MessageBody=record['body'],
                    MessageAttributes=record['messageAttributes'],
                    MessageGroupId=record['attributes']['MessageGroupId'],
                    MessageDeduplicationId=record['attributes']['MessageDeduplicationId']
                )
        return {}


@error_response
def lambda_handler(event, context):
    return EventTaskQueueSegmentationClass().handle(event=event,context=context)

def _sqs_attributes_cleaner(attributes):
    d = dict.fromkeys(attributes)
    for k in d:
        if isinstance(attributes[k], dict):
            subd = dict.fromkeys(attributes[k])
            for subk in subd:
                if not attributes[k][subk]:
                    del attributes[k][subk]
                else:
                    attributes[k][''.join(subk[:1].upper() + subk[1:])] = attributes[k].pop(subk)