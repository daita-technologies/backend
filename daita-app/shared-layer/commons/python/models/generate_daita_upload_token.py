import boto3
import time
import random
import hashlib
from datetime import datetime
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *

stringRandom = '0123456789qwertyuiopasdfghjklzxcvbnm'


def randomToken():
    m = hashlib.md5()
    now = str(datetime.now())
    m.update(now.encode('utf-8'))
    token = m.hexdigest()
    for _ in range(0, 15):
        token += stringRandom[random.randint(0, len(stringRandom)-1)]
    return token


class GenerateDaitaUploadTokenkItem():
    FIELD_IDENTITY_ID = "identity_id"
    FIELD_PROJECT_ID = "project_id"
    FIELD_TOKEN = "token"
    FIELD_ID_TOKEN = "id_token"
    FIELD_TTL = "time_to_live"
    FIELD_PROJECT_NAME = "project_name"

    def __init__(self) -> None:
        self.identity_id = ""
        self.token = ""
        self.id_token = ""
        self.project_id = ""
        self.ttl = 0
        self.project_name = ""

    def to_dict(self):
        dict_info = {
            self.FIELD_IDENTITY_ID: self.identity_id,
            self.FIELD_PROJECT_ID: self.project_id,
            self.FIELD_TOKEN: self.token,
            self.FIELD_TTL: self.ttl,
            self.FIELD_ID_TOKEN: self.id_token,
            self.FIELD_PROJECT_NAME: self.project_name
        }
        return dict_info

    def from_db_item(self, item_info):
        self.identity_id = item_info.get(self.FIELD_IDENTITY_ID)
        self.token = item_info.get(self.FIELD_TOKEN)
        self.project_id = item_info.get(self.FIELD_PROJECT_ID)
        self.ttl = item_info.get(self.FIELD_TTL)
        self.id_token = item_info.get(self.FIELD_ID_TOKEN)
        self.project_name = item_info.get(self.FIELD_PROJECT_NAME)
        return self

    @classmethod
    def create_new_item(cls, id_token, identity_id, project_id, project_name):
        object = cls()
        object.token = randomToken()
        object.identity_id = identity_id
        object.project_id = project_id
        object.id_token = id_token
        object.project_name = project_name
        object.ttl = 60*60 + int(time.time())
        return object


class GenerateDaitaUploadTokenModel():

    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name)
        self.IndexToken = table_name + '-1'

    def insert_new_token(self, item) -> None:
        response = self.table.put_item(
            Item=item.to_dict()
        )
        return

    def token_exsited(self, identity_id, project_id):
        response = self.table.query(KeyConditionExpression=Key('identity_id').eq(
            identity_id), FilterExpression=Attr('project_id').eq(project_id))

        if len(response['Items']) <= 0:
            return None

        return response['Items'][0]

    def create_new_token(self, id_token, identity_id, project_id, project_name):
        generate_token_item = GenerateDaitaUploadTokenkItem.create_new_item(id_token=id_token,
                                                                            identity_id=identity_id, project_id=project_id, project_name=project_name)

        self.insert_new_token(generate_token_item)
        return generate_token_item.token

    def query_by_token(self, token):
        resp = self.table.query(
            IndexName=self.IndexToken,
            KeyConditionExpression=Key('token').eq(token),
            Limit=1,
            ScanIndexForward=False
        )

        if len(resp['Items']) <= 0:
            return None

        return resp['Items'][0]
