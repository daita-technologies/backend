import codeop
import boto3
from botocore.exceptions import ClientError
from config import REGION
sqsClient = boto3.client('sqs')
sqsResourse = boto3.resource('sqs')
def getQueue(queue_name):
    try:
        response = sqsClient.get_queue_url(QueueName=queue_name)
    except ClientError as e:
        print(e)
        raise e
    return response['QueueUrl']

def countTaskInQueue(queue_id):    
    sqs = sqsResourse.get_queue_by_name(QueueName=queue_id)
    num_task_in_queue = len(sqs.receive_messages())
    print(f"QueueID:  {queue_id} has len: {num_task_in_queue}")
    return num_task_in_queue
"""
batches_input
batches_output
output:
    {
        input:
        output:
        api:

    }
"""
"""
if self.worker['process_type'] == 'AUGMENT':
    input_json = {
                    "images_paths":input_list,
                    "output_folder": output_dir,
                    "num_augments_per_image": self.worker['num_augments_per_image'],
                    "codes": [],
                    "type": "augmentation"
                    }
else:
    input_json = {
        "images_paths":input_list,
        "output_folder": output_dir,
        "type": "preprocessing",
        "codes": []

    }
"""
"""
host http://{}:8000/ai
"""


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
        numtask = countTaskInQueue(ec2['queque_id'])
        listNumberTaskQueueCurrent.append(numtask)
        if maxEc2Task < numtask:
            maxEc2Task = numtask
    flag = 0
    if maxEc2Task != 0:
        for index, numbertask in enumerate(listNumberTaskQueueCurrent):
            if numbertask != maxEc2Task:
                for _ in range(maxEc2Task - task +1):
                    input_request_ai = parserInputJson(type_method,code,num_augments_per_image,flag)
                    task = {
                            'request_json': input_request_ai,
                            'host': 'http://{}:8000/ai'.format(ec2IDs[index]['ip']),
                            'queue': getQueue(ec2IDs[index]['queque_id'])
                        }
                    listRequestAPI.append(task)
                    flag += 1
    
    for it in range(flag,length_batched):
        index =int(it%len(ec2IDs))
        input_request_ai = parserInputJson(type_method,code,num_augments_per_image,it)
        task = {
            'request_json': input_request_ai,
            'host': 'http://{}:8000/ai'.format(ec2IDs[index]['ip']),
            'queue': getQueue(ec2IDs[index]['queque_id'])
        }
        listRequestAPI.append(task)
        
    print("SHARE TASK")
    print(len(listRequestAPI),length_batched)
    print(listRequestAPI)
    return listRequestAPI