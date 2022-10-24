import boto3

class LambdaConst():

    FIELD_GROUP_NAME    = "group"
    FIELD_NAME          = "name"
    FIELD_VALUE         = "value"

    VALUE_GROUP = "anno"

    VALUE_NAME = ""

    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name)

        self.const