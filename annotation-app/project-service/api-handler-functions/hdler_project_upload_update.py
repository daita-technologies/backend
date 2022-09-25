import boto3
import json
import os
import uuid

from config import *
from response import *
from error_messages import *
from utils import convert_current_date_to_iso8601, aws_get_identity_id, get_num_prj
import const


from lambda_base_class import LambdaBaseClass


class ProjectAnnotationUploadUpdate(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
    def parser(self,body):
        self.id_token = body['id_token']
        
    def handle(self,event,context):
        

@error_response
def lambda_handler(event, context):
    return ProjectAnnotationUploadUpdate().handle(event=event,context=context)