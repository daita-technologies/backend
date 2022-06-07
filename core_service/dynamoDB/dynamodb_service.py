import boto3


class DynamoDBService:
    def __init__(self) -> None:
        self.db_client = boto3.client("dynamodb")

    def create_bd(
        self, table_name, ls_key_schema, billmode=None, provisionthrough=None
    ):

        va_key_schema = []
        va_attribute = []
        for item in ls_key_schema:
            va_attribute.append({"AttributeName": item[0], "AttributeType": item[2]})
            va_key_schema.append({"AttributeName": item[0], "KeyType": item[1]})
        try:
            self.db_client.create_table(
                TableName=table_name,
                AttributeDefinitions=va_attribute,
                KeySchema=va_key_schema,
                BillingMode="PAY_PER_REQUEST",
            )
        except Exception as e:
            if (
                e.response["Error"]["Code"] == "ResourceInUseException"
                and "Table already exists" in e.response["Error"]["Message"]
            ):
                if billmode and provisionthrough:
                    try:
                        self.db_client.update_table(
                            TableName=table_name,
                            BillingMode=billmode,
                            ProvisionedThroughput=provisionthrough,
                        )
                    except Exception as err:
                        pass
                print(e.response["Error"]["Message"])
