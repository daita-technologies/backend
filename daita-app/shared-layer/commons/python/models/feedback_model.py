import boto3

class Feedback(object):
    def __init__(self,TBL):
        self.db_client = boto3.resource('dynamodb')
        self.TBL = TBL

    def CreateItem(self, info):
        self.db_client.Table(self.TBL).put_item(Item={
            "ID": info["ID"],
            "name": info["name"],
            "content": info["content"],
            "images": info["images"],
            "created_time": info["created_time"],
        })

    def CheckKeyIsExist(self, ID):
        response = self.db_client.Table(self.TBL).get_item(Key={
            "ID": ID
        })
        if 'Item' in response:
            return True
        return False