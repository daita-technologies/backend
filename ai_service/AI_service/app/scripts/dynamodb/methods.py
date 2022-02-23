from os import path
import boto3

def scan_table(dynamo_client, *, TableName, **kwargs):
    """
    Generates all the items in a DynamoDB table.

    :param dynamo_client: A boto3 client for DynamoDB.
    :param TableName: The name of the table to scan.

    Other keyword arguments will be passed directly to the Scan operation.
    See https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Client.scan

    """
    paginator = dynamo_client.get_paginator("scan")

    for page in paginator.paginate(TableName=TableName, **kwargs):
        yield from page["Items"]

def get_data_method():
    method_db ={}
    db_client = boto3.client('dynamodb')
    for item in scan_table(db_client,TableName='methods'):
        method_db[item['method_name']['S']] =  item['method_id']['S']
    return method_db

# method_db = get_data_method()
