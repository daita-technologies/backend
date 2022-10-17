import boto3
import json
import os
import uuid
import re
import base64
from datetime import datetime 

from response import *

from lambda_base_class import LambdaBaseClass




class HandleStreamDataOriginAnnotation(LambdaBaseClass):
    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')   
        self.client_step_func= boto3.client('stepfunctions')
        self.s3 =  boto3.client('s3')
        self.sqsResourse = boto3.resource('sqs')

    def handle(self, event, context):
        records =  event['Records']
        listRecord = []
        print(f'logs :{records}')
        for record in records:
            if record['eventName'] == 'INSERT':
                tempItem =  {
                    'project_id': record['dynamodb']['Keys']['project_id']['S'],
                    'filename' : record['dynamodb']['Keys']['filename']['S'],
                    's3_key':record['dynamodb']['NewImage']['s3_key']['S']
                }
                listRecord.append(tempItem)    

            ### push task to sqs to  tracking
        input_folder=  str(base64.b64encode(str(datetime.now()).encode()).decode("ascii"))
        if len(listRecord) == 0:
            print('Nothing to generate')
            return {"message":"ok"}
        
        self.client_step_func.start_execution(
            stateMachineArn=os.environ["ECS_TASK_ARN"],
            input=json.dumps(
                {
                    'input_folder': input_folder,
                    'records': listRecord
                }
                )
        )        
        # queue = self.sqsResourse.get_queue_by_name(QueueName=os.environ['QUEUE'])
        # request_queue = {'records' :listRecord }
        # request_queue['output_directory'] = os.path.join(input_folder,'output')
        # queue.send_message(
        #                     MessageBody=json.dumps(request_queue),
        #                     MessageGroupId="push-task-segement-queue",
        #                     DelaySeconds=0,
        #                 )
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
# cluster = "segment-ecstask-ServiceApplication-1OPTNXI2VFIW7-ECSCluster-20iFW6ZFwY3Q"
# ecsTask = "arn:aws:ecs:us-east-2:737589818430:task-definition/segment-ecstask-ServiceApplication-1OPTNXI2VFIW7-TaskAISegmenationDefinition-4uPNYxdUAF3n:1"
# ecs = boto3.client('ecs')
# command = ["--input_json_path","data/sample/input.json","--output_folder","data/sample/output"]
# response = ecs.run_task(
#     cluster = cluster,
#     taskDefinition= ecsTask,
#     count=1,
#        overrides={
#             'containerOverrides': [
#                 {
#                     'name': 'test-ecs-task-ecs-segmentations',
#                     'command': command,
#                 },
#             ]
#         }
# )