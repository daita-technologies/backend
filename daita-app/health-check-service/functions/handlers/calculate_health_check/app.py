from typing import Dict, Union
import boto3
import json
import os
import logging
import traceback

import time
import datetime
from http import HTTPStatus

import healthcheck_list  # Import to register all preprocessing
from registry import HEALTHCHECK
from healthcheck_utils import read_image


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

RESPONSE_HEADER = {
    "access-control-allow-origin": "*",
	"access-control-allow-headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-Amz-User-Agent"
}

def generate_response(
    message: str,
    status_code: int = HTTPStatus.OK,
    headers: dict = {},
    data: dict = {},
    cookie: str = "",
    error: bool = False,
    is_in_stepfunction: bool = False
    ):

    headers.update(RESPONSE_HEADER)

    body = {
        "message": message,
        "data": data,
        "error": error
    }
    
    if is_in_stepfunction:
        return {
            "statusCode": status_code,            
            "body": body,
        }
    else:
        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(body),
            "isBase64Encoded": False
        }

def error_response(lambda_handler):
    def exception_handler(*args, **kwargs):
        try:
            return lambda_handler(*args, **kwargs)
        except Exception as exc:
            print(repr(exc))
            print(traceback.format_exc())
            messageRaw = str(repr(exc))            

            return(
                generate_response(
                    message= messageRaw.replace("Exception('", "").replace("')", "").replace("Exception(\"", "").replace("\")", ""),
                    error=True
                )
            )
            
    return exception_handler

class CalculateHealthCClass(LambdaBaseClass):
    
    KEY_DATA_TABLE_NAME = "data_table_name"
    KEY_NAME_PROJECT_ID = "project_id"

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()  

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        
        self.project_id = body[self.KEY_NAME_PROJECT_ID]
        self.data_table_name = body[self.KEY_DATA_TABLE_NAME]
        self.filename = body["file_s3"][0]
        self.s3_key = body["file_s3"][1]           

    def _check_input_value(self):
        pass
    
    def _calculate_healthcheck(self, image_s3_key):
        result: Dict[str, Union[int, float, str, None]] = {
            "file_name": None,
            "signal_to_noise_red_channel": None,
            "signal_to_noise_green_channel": None,
            "signal_to_noise_blue_channel": None,
            "sharpness": None,
            "contrast": None,
            "luminance": None,
            "file_size": None,
            "height": None,
            "width": None,
            "aspect_ratio": None,
            "mean_red_channel": None,
            "mean_green_channel": None,
            "mean_blue_channel": None,
            "extension": None,
        }

        print(f"Processing {image_s3_key}")
        if "s3://" not in image_s3_key:
            image_path = "s3://" + image_s3_key
        else:
            image_path = image_s3_key
            
        try:
            start = time.time()
            image = read_image(image_path, is_from_s3=True)

            # Check file name
            result["file_name"] = os.path.basename(image_path)

            # Check signal to noise of each channel
            snr_R, snr_G, snr_B = HEALTHCHECK["signal_to_noise"](image, image_path=image_path)
            result["signal_to_noise_red_channel"] = snr_R
            result["signal_to_noise_green_channel"] = snr_G
            result["signal_to_noise_blue_channel"] = snr_B

            # Check sharpeness
            sharpness = HEALTHCHECK["sharpness"](image, image_path=image_path)
            result["sharpness"] = sharpness

            # Check contrast
            contrast = HEALTHCHECK["contrast"](image, image_path=image_path)
            result["contrast"] = contrast

            # Check luminance
            luminance = HEALTHCHECK["luminance"](image, image_path=image_path)
            result["luminance"] = luminance

            # Check file size
            file_size_in_mb = HEALTHCHECK["file_size"](image, image_path=image_path)
            result["file_size"] = file_size_in_mb

            # Check height, width and aspect ratio
            height, width, aspect_ratio = HEALTHCHECK["height_width_aspect_ratio"](image, image_path=image_path)
            result["height"] = height
            result["width"] = width
            result["aspect_ratio"] = aspect_ratio

            # Check mean of each channel
            mean_red_channel = HEALTHCHECK["mean_red_channel"](image, image_path=image_path)
            mean_green_channel = HEALTHCHECK["mean_green_channel"](image, image_path=image_path)
            mean_blue_channel = HEALTHCHECK["mean_blue_channel"](image, image_path=image_path)
            result["mean_red_channel"] = mean_red_channel
            result["mean_green_channel"] = mean_green_channel
            result["mean_blue_channel"] = mean_blue_channel

            # Check extension
            extension = HEALTHCHECK["extension"](image, image_path=image_path)
            result["extension"] = extension

            end = time.time()
            print(result)
            print(f"Done processing {image_path}: {round(end - start, 4)} seconds")
            return result

        except Exception:
            print(result)
            print(f"Error processing {image_path}: {traceback.format_exc()} !!!")
            return result

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)           
        
        ### calculate health check
        result = self._calculate_healthcheck(self.s3_key)  
                
        return {
            self.KEY_NAME_PROJECT_ID: self.project_id,
            self.KEY_DATA_TABLE_NAME: self.data_table_name,
            "healthcheck": result
        }
       

@error_response
def lambda_handler(event, context):

    return CalculateHealthCClass().handle(event, context)

    