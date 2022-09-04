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
    def convert_to_image_batches(self, data):
        def generator():
            yield from data
        return batcher(generator(), 50)

    def handle(self, event, context):
        res = {"batches":[it for it in self.convert_to_image_batches(event['detail']['body'])]}
        return res


@error_response
def lambda_handler(event, context):
    return divdeThumbnailsImageCls().handle(event, context)
