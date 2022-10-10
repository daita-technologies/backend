import boto3
import json
import os
import uuid


from response import *

from lambda_base_class import LambdaBaseClass

class HandleStreamDataOriginAnnotation(LambdaBaseClass):
    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')   
        self.ecs_task = boto3.client('ecs')

    def handle(self, event, context):
    
        records =  event['Records']
        listRecord = []
        print(f'logs :{records}')
        for record in records:
            # if record['eventName'] == 'INSERT':
            tempItem =  {
                'project_id': record['dynamodb']['Keys']['project_id']['S'],
                'filename' : record['dynamodb']['Keys']['filename']['S'],
                'table': record['eventSourceARN'].split(':')[5].split('/')[1],
                's3_urls':record['dynamodb']['NewImage']['s3_key']['S']
            }
            listRecord.append(tempItem)    
        if len(listRecord) == 0:
            print('Nothing to generate')
            return {"message":"ok"}
        self.client_step_func.start_execution(
            stateMachineArn=os.environ["ECS_TASK_ARN"],
            input=json.dumps(listRecord)
        )        
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "ok": "ok"
                },
        )

@error_response
def lambda_handler(event, context):
    return HandleStreamDataOriginAnnotation().handle(event=event,context=context)
