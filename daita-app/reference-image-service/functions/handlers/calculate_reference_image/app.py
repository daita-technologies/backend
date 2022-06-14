from typing import Dict, Union
import boto3
import json
import os
import logging
import traceback

from preprocessor import Preprocessor


class SystemParameterStore():
    
    def __init__(self) -> None:
        self.ssm = boto3.client('ssm', 'us-east-2')
        
    def get_param(self, name):
        return self.ssm.get_parameter(Name=name,WithDecryption=False)['Parameter']['Value']     
    
    
class LambdaBaseClass(object):
    
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(os.environ["LOGGING"])

    def handle(self, event, context):        
        raise NotImplementedError

    @classmethod
    def parse_body(cls, func):
        def parser(object, event):
            if type(event['body']) is str:
                body = json.loads(event['body'])
            else:
                body = event['body']
                
            object.logger.info("Body: {}".format(body))
            try:
                print("Before call func")
                func(object, body)
            except Exception as e:
                raise Exception("Invalid Json") from e
            object._check_input_value()
            return 
        
        return parser 

    def _check_input_value(self):        
        pass
        return

class RICalculateClass(LambdaBaseClass):
    
    KEY_NAME_PROJECT_ID = "project_id"
    KEY_NAME_IDENTITY_ID = "identity_id"
    KEY_NAME_LS_METHOD_ID = "ls_method_id"
    KEY_NAME_S3_KEY_PATH = "s3_key_path"
    KEY_NAME_TASK_ID = "task_id"
    KEY_NAME_INDEX = "index"
    KEY_NAME_BUCKET = "bucket"

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()  
        self.s3 = boto3.client('s3')  
        max_width = int(self.const.get_param(os.environ["MAX_WIDTH_RESOLUTION_IMG"]))
        max_height = int(self.const.get_param(os.environ["MAX_HEIGHT_RESOLUTION_IMG"]))
        self.preprocessor = Preprocessor(max_width=max_width, max_height=max_height)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")   

        self.project_id = body[self.KEY_NAME_PROJECT_ID]
        self.identity_id = body[self.KEY_NAME_IDENTITY_ID]
        self.bucket = body[self.KEY_NAME_BUCKET]
        self.s3_data_path = body[self.KEY_NAME_S3_KEY_PATH]
        self.ls_method_id = body[self.KEY_NAME_LS_METHOD_ID]
        self.index = body[self.KEY_NAME_INDEX]

    def _check_input_value(self):
        pass   

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)       

        ### read data from s3 and get data with index        
        resultS3 = self.s3.get_object(Bucket=self.bucket, Key=self.s3_data_path)
        ls_data = json.loads(resultS3["Body"].read().decode())
        data = ls_data[self.index]
        print("data after get from index: ",data)
        
        ### calculate info of reference image
        refer_dict, update_data, overlimit_image = self.preprocessor.get_reference_image_paths(data, self.ls_method_id)
        save_dict = {
            "input_data": update_data,
            "reference": refer_dict
        }

        ### write data to json s3        
        folder = "/".join(self.s3_data_path.split("/")[:-1])
        s3_name = f"output/RI_{self.index}_output_references.json"
        s3_key_path = os.path.join(folder, s3_name)
        self.s3.put_object(
            Body=json.dumps(save_dict),
            Bucket= self.bucket,
            Key= s3_key_path
        )         
        s3_name_over = f"output/RI_{self.index}_overlimit_image.json"
        s3_key_path_over = os.path.join(folder, s3_name_over)
        self.s3.put_object(
            Body=json.dumps(overlimit_image),
            Bucket= self.bucket,
            Key= s3_key_path_over
        )  
                
        return {
            self.KEY_NAME_INDEX: self.index,
            "s3_name": s3_name,
            "s3_overlimit": s3_name_over
        }

       
def lambda_handler(event, context):

    return RICalculateClass().handle(event, context)

    