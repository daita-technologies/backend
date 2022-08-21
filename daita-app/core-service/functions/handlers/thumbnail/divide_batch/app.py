import boto3
from error_messages import *
from response import *
from config import *
from boto3.dynamodb.conditions import Key, Attr
from lambda_base_class import LambdaBaseClass
from itertools import chain, islice


def batcher(iterable, size):
    iterator = iter(iterable)
    for first in iterator:
        yield list(chain([first], islice(iterator, size - 1)))


class divdeThumbnailsImageCls(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    def parser(self, body):
        self.project_id = body['project_id']
        self.type = body['type']
        self.table = boto3.resource('dynamodb').Table(self.type)

    def convert_to_image_batches(self, data):
        images = []
        for it in data:
            if not 'thumbnail' in it or not bool(it['thumbnail']):
                images.append(it['s3_key'])

        def generator():
            yield from images
        return batcher(generator(), 100)

    def handle(self, event, batch):
        self.parser(event['body'])
        result = {'batches': [], 'project_id': self.project_id,
                  'data_type': self.type}
        queryResponse = self.table.query(
            KeyConditionExpression=Key(
                'project_id').eq(self.project_id), Limit=200
        )
        items = []
        if 'Items' in queryResponse:
            items = queryResponse['Items']

        while 'LastEvaluatedKey' in queryResponse:
            key = queryResponse['LastEvaluatedKey']
            queryResponse = self.table.query(
                KeyConditionExpression=Key(
                    'project_id').eq(self.project_id),
                Limit=200, ExclusiveStartKey=key
            )
            items.extend(queryResponse['Items'])
        result['batches'] = self.convert_to_image_batches(items)
        return result


@error_response
def lambda_handler(event, context):
    return divdeThumbnailsImageCls().handle(event, context)
