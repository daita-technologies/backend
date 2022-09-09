import boto3
import os
class EventUser:
    def __init__(self):
           self.db_client = boto3.resource('dynamodb',region_name=os.environ['REGION'])
           self.TBL = os.environ['TBL_EVENTUSER']
    def create_item(self,info):
        self.db_client.Table(self.TBL).put_item(Item={
            'event_ID':info['event_ID'],
            'type':info['type']
            })
    def create_item_cognito(self,info):
        self.db_client.Table(self.TBL).put_item(Item={
           'event_ID':info['event_ID'],
            'type':info['type'],
            'code':info['code']
        })

    def delete_item(self,info):
        self.db_client.Table(self.TBL).delete_item(
        Key={
            'event_ID': info['event_ID'],
            'type': info['type']
        }
    )

    def get_code_oauth2(self,info):
        response = self.db_client.Table(self.TBL).get_item(
            Key={
                   'event_ID':info['event_ID'],
                   'type':info['type']
                                 }
        )
        return response['Item']

    def find_item(self,info):
        response = self.db_client.Table(self.TBL).get_item(
              Key={
                   'event_ID':info['event_ID'],
                   'type':info['type']
                                 }
        )
        return True if 'Item' in response else False
model = EventUser()


def CreateEventUserLogin(sub):
    model.create_item(info={
        'event_ID':sub,
        'type':'AUTH'
    })

def CreateEventUserLoginOauth2(sub,code):
    model.create_item_cognito(info={
        'event_ID':sub,
        'type':'AUTH',
        'code':code
    })

def get_code_oauth2_cognito(sub):
    return model.get_code_oauth2(
        info={
            'event_ID':sub,
            'type':'AUTH'
        }
    )['code']


def CheckEventUserLogin(sub):
    return model.find_item(info={
        'event_ID':sub,
        'type':'AUTH'
    })
def EventUserLogout(sub):
    model.delete_item(info={
        'event_ID':sub,
        'type':'AUTH'
    })