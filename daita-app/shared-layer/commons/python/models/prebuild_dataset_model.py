import boto3
from boto3.dynamodb.conditions import Key, Attr

class PrebuildDatasetModel():
    FIELD_NAME = "name"
    FIELD_S3_KEY = "s3_key"
    FIELD_VISUAL_NAME = "visual_name"
    FIELD_IS_ACTIVE = "is_active"
    FIELD_TOTAL_IMAGES = "total_images"

    def __init__(self, table_name) -> None:
        self.tablename = table_name
        self.table = boto3.resource('dynamodb').Table(table_name)

    def get_list_prebuild_dataset(self):
        response = self.table.scan(
                    FilterExpression=Attr(self.FIELD_IS_ACTIVE).eq(True)
                )
        items = response["Items"]

        return items
        
    def get_const_with_code(self, code, type="THRESHOLD"):
        response = self.table.get_item(
            Key = {
                'code': code,
                'type': type
            }
        )
        return response.get("Item")[self.FIELD_NUM_VALUE]