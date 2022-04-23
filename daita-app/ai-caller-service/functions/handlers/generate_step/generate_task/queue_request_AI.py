import json
import boto3
import os
from botocore.exceptions import ClientError
from config import REGION

sqsClient = boto3.client('sqs',REGION)
sqsResourse = boto3.resource('sqs',REGION)

def getQueue(queue_name_env):
    try:
        response = sqsClient.get_queue_url(QueueName=os.environ[queue_name_env])
    except ClientError as e:
        print(e)
        raise e
    return response['QueueUrl']

def countTaskInQueue(queue_id):
    # get_queue_attributes
    # sqsName = sqsResourse.get_queue_by_name(QueueName=queue_id)
    response = sqsClient.get_queue_attributes(
                            QueueUrl=getQueue(queue_id),
                            AttributeNames=[
                                'ApproximateNumberOfMessages'
                            ]
                        )
    num_task_in_queue = response['Attributes']['ApproximateNumberOfMessages']
    print(f"QueueID:  {queue_id} has len: {num_task_in_queue}")
    return int(num_task_in_queue)

def assignTaskToEc2(ec2Instances,data,type_method,num_augments_per_image,code):
    listRequestAPI = []
    listNumberTaskQueueCurrent= []
    ec2IDs= []
    maxEc2Task = 0
    def parserInputJson(method,code,num_augments_per_image,index):
        input_request_ai= {}
        if method == 'AUGMENT':
            input_request_ai = {
                                "images_paths":data['batches_input'][index],
                                "output_folder": data['batches_output'][index],
                                "num_augments_per_image":num_augments_per_image,
                                "codes":code ,
                                "type": "augmentation"
                                }       
        else:
            input_request_ai = {
                    "images_paths":data['batches_input'][index],
                    "output_folder": data['batches_output'][index],
                    "type": "preprocessing",
                    "codes": code
                }
        return input_request_ai
    # get current task 
    length_batched = len(data['batches_input'])
    
    for ec2 in ec2Instances:
        ec2IDs.append(ec2)
        numtask = countTaskInQueue(ec2['queue_env_name'])
        listNumberTaskQueueCurrent.append(numtask)
        if maxEc2Task < numtask:
            maxEc2Task = numtask
    flag = 0
    if maxEc2Task != 0:
        for index, numbertask in enumerate(listNumberTaskQueueCurrent):
            if numbertask != maxEc2Task and flag < length_batched:
                for _ in range(maxEc2Task - numbertask +1):
                    input_request_ai = parserInputJson(type_method,code,num_augments_per_image,flag)
                    task = {
                            'request_json': input_request_ai,
                            'host': 'http://{}:8000/ai'.format(ec2IDs[index]['ip']),
                            'queue': os.environ[ec2IDs[index]['queue_env_name']],
                            'ec2_id': ec2IDs[index]["ec2_id"]
                        }
                    queueSQS = sqsResourse.get_queue_by_name(QueueName=task['queue'])
                    queueSQS.send_message(
                            MessageBody=json.dumps(task),
                            MessageGroupId="RequestAI",
                            DelaySeconds=0,
                        )
                    listRequestAPI.append(task)
                    flag += 1
                    if flag >= length_batched:break
    
    for it in range(flag,length_batched):
        index =int(it%len(ec2IDs))
        input_request_ai = parserInputJson(type_method,code,num_augments_per_image,it)
        task = {
            'request_json': input_request_ai,
            'host': 'http://{}:8000/ai'.format(ec2IDs[index]['ip']),
            'queue': os.environ[ec2IDs[index]['queue_env_name']],
            'ec2_id': ec2IDs[index]["ec2_id"]
        }
        queueSQS = sqsResourse.get_queue_by_name(QueueName=task['queue'])
        queueSQS.send_message(
                            MessageBody=json.dumps(task),
                            MessageGroupId="RequestAI",
                            DelaySeconds=0,
                        )
        listRequestAPI.append(task)
        
    print("SHARE TASK")
    print(len(listRequestAPI),length_batched)
    print(listRequestAPI)
    return listRequestAPI