import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from typing import List


class MethodItem:

    FIELD_METHOD_ID = "method_id"
    FIELD_METHOD_NAME = "method_name"

    def __init__(self) -> None:
        self.method_id = ""
        self.method_name = ""
        self.item_db = None

    @classmethod
    def from_db_item(cls, item_info):
        if item_info is None:
            return None
        else:
            object = cls()
            object.item_db = item_info

            object.method_id = item_info.get(object.FIELD_METHOD_ID)
            object.method_name = item_info.get(object.FIELD_METHOD_NAME)

            return object


class MethodModel:
    def __init__(self, table_name) -> None:
        self.table = boto3.resource("dynamodb").Table(table_name)

    def get_all_methods(self) -> List[MethodItem]:
        response = self.table.scan()
        items = response["Items"]

        return [MethodItem.from_db_item(item) for item in items]
