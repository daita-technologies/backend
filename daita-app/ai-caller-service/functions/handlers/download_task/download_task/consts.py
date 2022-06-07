from urllib import response
import boto3
from botocore.exceptions import ClientError


class ConstTbl(object):
    def __init__(self):
        self.db_client = boto3.resource("dynamodb", region_name="us-east-2")

    def get_num_value(self, code, threshold):
        try:
            response = self.db_client.Table("consts").get_item(
                Key={"code": code, "type": threshold}
            )
        except ClientError as e:
            print(e.response["Error"]["Message"])
            if code == "limit_request_batchsize_ai":
                return 8
        return response["Item"]["num_value"]
