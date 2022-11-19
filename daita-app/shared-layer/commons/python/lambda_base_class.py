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
        def parser(object, event, is_event_as_body = False):
            if is_event_as_body:
                body = event
            else:
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

    def get_identity(self, id_token, user_pool_id=None, identity_pool_id=None):
        if user_pool_id is None or identity_pool_id is None:
            identity = aws_get_identity_id(id_token)
        else:
            identity = aws_get_identity_id(id_token=id_token,
                                 USER_POOL_ID=user_pool_id, IDENTITY_POOL_ID=identity_pool_id)
        self.logger.info(f"identity: {identity}")
        return identity

    def invoke_lambda_func(self, function_name, body_info, type_request="RequestResponse"):
        lambdaInvokeClient = boto3.client('lambda')
        lambdaInvokeReq = lambdaInvokeClient.invoke(
            FunctionName=function_name,
            Payload=json.dumps({'body': body_info}),
            InvocationType=type_request,
        )

        return json.loads(lambdaInvokeReq['Payload'].read().decode("utf-8"))
