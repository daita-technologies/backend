import boto3
import json
import os
import uuid


from response import *

from lambda_base_class import LambdaBaseClass


class ProjectCloneClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')   
        self.client_step_func = boto3.client('stepfunctions')
        

    @LambdaBaseClass.parse_body
    def parser(self, body):
        print(f"body in main_parser: {body}")

    def handle(self, event, context):
    
        ### parse body
        self.parser(event)
        
        ### call async step function
        stepfunction_input = {
            # "identity_id": identity_id,
        }
        response = self.client_step_func.start_execution(
            stateMachineArn=os.environ["SM_CLONE_PROJECT_ARN"],
            input=json.dumps(stepfunction_input)
        )        
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "ok": "ok"
                },
        )

@error_response
def lambda_handler(event, context):

    return ProjectCloneClass().handle(event, context)