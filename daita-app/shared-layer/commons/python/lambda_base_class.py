import logging
import os
from identity_check import *
import json
from load_env_lambda_function import LambdaEnv

class LambdaBaseClass(object):
    
    def __init__(self) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(os.environ["LOGGING"])
        self.env = LambdaEnv()

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
                raise Exception(MESS_INVALID_JSON_INPUT) from e
            object._check_input_value()
            return 
        
        return parser 

    def _check_input_value(self):        
        pass
        return

    def get_identity(self, id_token):
        identity = aws_get_identity_id(id_token)
        self.logger.info(f"identity: {identity}")
        return identity