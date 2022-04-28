import boto3
import time
from config import REGION
ec2_resource = boto3.resource('ec2', region_name=REGION)
clientEc2 = boto3.client('ec2',region_name=REGION)

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
                instance = ec2_resource.Instance(item['ec2_id']['S'])
                ip = startEc2(instance)
                EC2Free.append({'ec2_id':item['ec2_id']['S'],'queue_env_name':item['queue_env_name']['S'],'ip':ip})
        # print(EC2Free)
        return EC2Free

def start_instance(instance):
    print('Instance id {ec2_id} stopped => start now')
    _ = instance.start()
    instance.load()
    while instance.state['Name'] != 'running':
        if instance.state['Name'] == 'running':
            print('Running')
            pass
        else:
            time.sleep(5)
            instance.load()
            print('status: ', instance.state['Name'])
            pass
    return

def startEc2(instance):
    if instance.state['Name'] == 'stopped':
        start_instance(instance=instance)
    elif instance.state['Name'] == 'stopping':
        instance.load()
        while instance.state['Name'] != 'stopped':
                time.sleep(20)
                instance.load()
                pass
        print('Wait ec2 stopped to start')
        start_instance(instance)
    return instance.public_ip_address