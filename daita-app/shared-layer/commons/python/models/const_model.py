import boto3

class ConstModel():
    FIELD_CODE = "code"
    FIELD_TYPE = "type"
    FIELD_NUM_VALUE = "num_value"

    def __init__(self) -> None:
        self.tablename = "consts"
        self.table = boto3.resource('dynamodb').Table("consts")
        
    def get_const_with_code(self, code, type="THRESHOLD"):
        response = self.table.get_item(
            Key = {
                'code': code,
                'type': type
            }
        )
        return response.get("Item")[self.FIELD_NUM_VALUE]
        
