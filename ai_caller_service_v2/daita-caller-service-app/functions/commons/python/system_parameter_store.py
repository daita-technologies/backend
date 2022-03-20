import json
import boto3


class SystemParameterStore():

    def __init__(self) -> None:
        self.ssm = boto3.client('ssm', 'us-east-2')
        self.limit_prepro_times = self.ssm.get_parameter(Name='LimitPreprocessTimes',WithDecryption=False)['Parameter']['Value']
        self.limit_augment_times = self.ssm.get_parameter(Name='LimitAugmentTimes',WithDecryption=False)['Parameter']['Value']  
