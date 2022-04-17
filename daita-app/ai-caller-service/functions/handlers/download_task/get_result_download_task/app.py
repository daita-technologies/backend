
import time
import json
import boto3
import random
import glob
import threading
import os
import queue
import re
from itertools import chain, islice
from datetime import datetime
from config import *
from response import *
from utils import *
from identity_check import *

@error_response
def lambda_handler(event, context):
    result = None
    for it in event:
        if isinstance(it,dict):
            result = it
    return result