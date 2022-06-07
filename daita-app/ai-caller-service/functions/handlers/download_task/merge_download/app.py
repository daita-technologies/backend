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
from s3_utils import split

s3 = boto3.client("s3")


@error_response
def lambda_handler(event, context):
    if "reference_images" in event:
        root_efs = os.environ["ROOTEFS"]
        prefix_pwd = os.path.join(os.environ["EFSPATH"], event["task_id"])
        reference_images_folder = os.path.join(prefix_pwd, "reference_images")
        os.makedirs(reference_images_folder, exist_ok=True)
        for k, v in event["reference_images"].items():
            bucket, filename = split(v)
            basename = os.path.basename(filename)
            new_image = os.path.join(reference_images_folder, basename)
            s3.download_file(bucket, filename, new_image)
            event["reference_images"][k] = root_efs + new_image
    return event
