import logging
import os
import json


class LambdaBaseClass(object):
    
    def __init__(self) -> None:
        pass


    def handle(self, event, context):        
        raise NotImplementedError

    @classmethod
    def parse_body(cls, func):
        def parser(object, event):
            if type(event['body']) is str:
                body = json.loads(event['body'])
            else:
                body = event['body']
                
            print("Body: {}".format(body))
            try:
                print("Before call func")
                func(object, body)
            except Exception as e:
                raise Exception("") from e
            object._check_input_value()
            return 
        
        return parser 

    def _check_input_value(self):        
        pass
        return
