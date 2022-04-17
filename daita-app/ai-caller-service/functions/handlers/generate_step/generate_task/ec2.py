import boto3
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
                ip = instance.public_ip_address
                EC2Free.append({'ec2_id':item['ec2_id']['S'],'queque_id':item['queque_id']['S'],'ip':ip})
        print(EC2Free)
        return EC2Free


def startEc2(instance_id):
    instance = ec2_resource.Instance(instance_id)
    if instance.state['Name'] == 'stopped':
        try:
            clientEc2.start_instances(InstanceIds=[instance_id])
        except Exception as e:
            print("ec2 :",e)
            raise e