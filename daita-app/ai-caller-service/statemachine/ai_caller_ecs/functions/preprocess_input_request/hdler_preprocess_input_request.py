import shutil
import time
import json
import boto3
import random
from datetime import datetime
import requests
import queue
import threading
from itertools import chain, islice
import os
from config import *
from lambda_base_class import LambdaBaseClass
from response import *
from utils import *
from identity_check import *
from models.generate_task_model import GenerateTaskModel
from models.task_model import TaskModel


class PreprocessInputRequestClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.task_model = TaskModel(self.env.TABLE_GENERATE_TASK, None)
        self.generate_task_model = GenerateTaskModel(self.env.TABLE_GENERATE_TASK)

    @LambdaBaseClass.parse_body
    def parser(self, body):
        pass

    def handle(self, event, context):
        ### parse body
        self.parser(event, is_event_as_body=True)

        

        return {
            'response': self.response
        }

@error_response
def lambda_handler(event, context):
    return PreprocessInputRequestClass().handle(event=event,  context=context)