import json
import boto3


class SystemParameterStore():

    def __init__(self) -> None:
        self.ssm = boto3.client('ssm', 'us-east-2')
        
    def get_param(self, name):
        return self.ssm.get_parameter(Name=name,WithDecryption=False)['Parameter']['Value']         
