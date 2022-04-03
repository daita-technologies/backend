import boto3


class EC2Model(object):
    def __init__(self):
        self.db_client = boto3.resource('dynamodb')
        self.TBL = 'ec2'
    
    def scanTable(self,TableName,**kwargs):
        paginator = self.db_client.get_paginator("scan")
        for item in paginator.paginate(TableName=TableName,**kwargs):
            yield from item['Items']

    def getFreeEc2(self):
        EC2Free = []
        for item in self.scanTable(TableName=self.TBL):
            if item['assi_id']['S'] == 'free':
                EC2Free.append({'ec2_id':item['ec2_id']['S'],'queue_id':item['queque_id']['S']})
        return EC2Free