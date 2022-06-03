import boto3
import json
import os
import time
from boto3.dynamodb.conditions import Key, Attr
from models.generate_task_model import GenerateTaskModel
from models.task_model import TaskModel
from config import *
from response import *
from utils import *
from identity_check import *

generate_task_model = GenerateTaskModel(os.environ["TABLE_GENERATE_TASK"])
task_model = TaskModel(os.environ["TABLE_GENERATE_TASK"],None)

sqsClient = boto3.client('sqs',REGION)
sqsResourse = boto3.resource('sqs',REGION)
client_events = boto3.client('events')  

@error_response
def lambda_handler(event, context):
    timeout_start = time.time()
    db_resource = boto3.resource('dynamodb',REGION)
    
    while True:
        if time.time() - timeout_start >= 45:
            break
        queueSQS = sqsResourse.get_queue_by_name(QueueName=os.environ['TASK_QUEUE'])
        QueueResp = queueSQS.receive_messages(VisibilityTimeout=10,
            WaitTimeSeconds=0,MaxNumberOfMessages=10)
        pushedMessage = 0 
        maxPushedMessage = int(os.environ.get('MAX_CONCURRENCY_TASKS','2'))
        for index ,message in enumerate(QueueResp) :
            body = json.loads(message.body)
            detail = body["detail"]
            item = generate_task_model.get_task_info(detail['identity_id'] ,detail['task_id'])
            
            print(item.status,item.waitingInQueue)

            if item.status == 'FINISH' or item.status == 'CANCEL' or item.status == 'FINISH_ERROR' or item.status == 'ERROR':
                message.delete()
            if item.status != 'PENDING' or not item.waitingInQueue:
                pushedMessage += 1
            elif item.status == 'PENDING' and pushedMessage < maxPushedMessage and item.waitingInQueue:
                response = client_events.put_events(
                                    Entries=[
                                        {
                                            'Source': 'source.events',
                                            'DetailType': 'lambda.event',
                                            'Detail': json.dumps(detail),
                                            'EventBusName': os.environ["EVENT_BUS_NAME"]
                                        },
                                    ]
                                )
                generate_task_model.update_task_dequeue(detail['identity_id'] ,detail['task_id'])
                pushedMessage += 1
                print(response)
            
            if item.status == 'CANCEL' and int(item.number_finished) != 0:
                task_model.update_number_files(task_id = item.task_id, identity_id =item.identity_id,num_finish = 0)
                if item.process_type == 'AUGMENT':
                    tableDataGen = db_resource.Table(os.environ['TABLE_DATA_AUGMENT'])
                else:
                    tableDataGen = db_resource.Table(os.environ['TABLE_DATA_PREPROCESS'])
                
                queryResponse = tableDataGen.query(
                        KeyConditionExpression=Key('project_id').eq(item.project_id),
                        FilterExpression=Attr('s3_key').contains(item.task_id)
                )
                
                print(f"The number files will be deleted {len(queryResponse['Items'])}")

                if len(queryResponse['Items']) > 0 :
                    total_file = len(queryResponse['Items'])
                    total_size = 0
                    with tableDataGen.batch_writer() as batch:
                        for each in queryResponse['Items']:
                            tableDataGen.delete_item(Key={
                                'project_id': each['project_id'],
                                'filename':each['filename']
                            })
                            total_size += each['size']
                    # Update Table T_PROJECT_SUMMARY 
            
                    prj_sum_all = db_resource.Table(os.environ['T_PROJECT_SUMMARY'])
                    responsePrjSumAll = prj_sum_all.get_item( Key = {
                            "project_id":detail['project_id'] ,
                            "type": item.process_type
                        })
                    print(responsePrjSumAll['Item'])
                    if not 'Item' in responsePrjSumAll:
                        return {}
                    itemResponseProjSumAll = responsePrjSumAll['Item']
                    prj_sum_all.update_item(Key = {
                                'project_id': detail['project_id'],
                                'type': item.process_type
                            },
                            ExpressionAttributeNames = {
                                '#SI': 'total_size',
                                '#COU': 'count',  
                            },
                            ExpressionAttributeValues = {
                                ':si': itemResponseProjSumAll['total_size'] - total_size,
                                ':cou': itemResponseProjSumAll['count'] -total_file 
                            },
                            UpdateExpression='SET #SI = :si, #COU = :cou' 
                    )
        
        time.sleep(2)
    
    return {}