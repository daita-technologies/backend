import boto3
import time
from config import *
from response import *
from utils import *
from identity_check import *
from config import REGION
ec2_resource = boto3.resource('ec2', region_name=REGION)
clientEc2 = boto3.client('ec2',region_name=REGION)
sqsClient = boto3.client('sqs',REGION)

def getQueue(queue_name_env):
    try:
        response = sqsClient.get_queue_url(QueueName=os.environ[queue_name_env])
    except Exception as e:
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

class EC2Model(object):
    def __init__(self):
        self.db_client = boto3.client('dynamodb')
        self.TBL = 'ec2'
    
    def scanTable(self,TableName,**kwargs):
        paginator = self.db_client.get_paginator("scan")
        for item in paginator.paginate(TableName=TableName,**kwargs):
            yield from item['Items']

    def getFreeEc2(self):
        EC2Free = []
        for item in self.scanTable(TableName=self.TBL):
            if item['assi_id']['S'] == 'free':
                EC2Free.append({
                        'ec2_id': item['ec2_id']['S'],
                        'queue_env_name': item['queue_env_name']['S'],
                        'is_enable_cronjob': item['is_enable_cronjob']['BOOL']
                    })
        return EC2Free

client = boto3.client('stepfunctions')

def stopEc2(ec2_id, is_enable_scronj):
    if not is_enable_scronj:
        return

    instance = ec2_resource.Instance(ec2_id)
    if instance is None:
        raise Exception(f"Instance id {ec2_id} does not exist")

    if instance.state['Name'] == 'stopped':
        print('Instance id {ec2_id} stopped => no process')
        
    elif instance.state['Name'] == 'running':
        print('Instance id {ec2_id} running => stop')
        instance.stop()

@error_response
def lambda_handler(event, context):
    print("==================== START a schedule job =====================")

    step_arn = os.environ["SF_CALL_SERVICE"]

    response = client.list_executions(
        stateMachineArn=step_arn,
        statusFilter='RUNNING',
        maxResults=50
    )
    ls_running_exe = response['executions']

    ec2Model = EC2Model()
    ec2free = ec2Model.getFreeEc2()
    
    if len(ls_running_exe) > 0:
        print("----- Exist running executions => check queue of each ec2 ---")
        ### purge all messages in queue        
        for ec2 in ec2free:  
            numTaskInEC2 = countTaskInQueue(ec2['queue_env_name'])          
            if numTaskInEC2 == 0:
                print("STOP EC2 :",ec2['ec2_id'])
                stopEc2(ec2['ec2_id'], ec2['is_enable_cronjob'])
    else:
        
        print("--- No running executions now, so stop all free ec2 -----")
        for ec2 in ec2free:  
            print("STOP EC2 :",ec2['ec2_id'])
            stopEc2(ec2['ec2_id'], ec2['is_enable_cronjob'])
    return