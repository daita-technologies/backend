import boto3
import json
import os

import numpy as np
from config import *
from response import *
from error_messages import *
from identity_check import *
from utils import get_bucket_key_from_s3_uri

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.reference_image_info_model import ReferenceImageInfoModel
from models.task_model import TaskModel
from models.project_model import ProjectModel
from typing import List


def get_index_of_median_value(array: Union[List[float], np.ndarray]) -> int:
    """
    Find index of the median value in a list or 1-D arry
    """
    index: int = np.argsort(array)[len(array) // 2]
    return index

def get_index_of_sorted(array: Union[List[float], np.ndarray]) -> int:
    """
    Find index base on the sorted og singnal ratios
    """
    idxs_sorted: List[int] = sorted(
        range(len(array)),
        key=lambda i: array[i],
    )
    idx: int = idxs_sorted[0]
    return idx

DICT_POSTPROCESS_METHOD = {
    "median": get_index_of_median_value,
    "sorted": get_index_of_sorted
}

class MergeResultClass(LambdaBaseClass):
    
    KEY_DATA_TABLE_NAME = "data_table_name"

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore() 
        self.s3 = boto3.client('s3')
        self.reference_info_model = ReferenceImageInfoModel(os.environ["TABLE_REFERENCE_IMAGE_INFO"])
        self.task_model = TaskModel(os.environ["TABLE_REFERENCE_IMAGE_TASK"])
        self.project_model = ProjectModel(os.environ["TABLE_PROJECT"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        
        self.logger.debug(f"body in main_parser: {body}")
        self.project_id = body["detail"]["project_id"]  
        self.task_id = body["detail"]["task_id"]
        self.identity_id = body["detail"]["identity_id"]
        self.ls_method_id = body["detail"]["ls_method_id"]
        self.project_name = body["detail"][KEY_NAME_PROJECT_NAME]
        self.ls_method_choose = body["detail"][KEY_NAME_LS_METHOD_CHOOSE]

        self.s3_key_path = body["body"]["s3_key_path"]
        self.result_calculate = body["result_map"]
        self.bucket = body["body"]["bucket"]

    def _check_input_value(self):
        pass

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)   
        
        ### get folder
        folder = "/".join(self.s3_key_path.split("/")[:-1])
        print("folder: ", folder)

        ### get data from json file in s3
        paths = [f'{folder}/{x["s3_name"]}' for x in self.result_calculate]
        ls_data = []
        for path in paths:
            resultS3 = self.s3.get_object(Bucket=self.bucket, Key=path)
            ls_data.append(json.loads(resultS3["Body"].read().decode()))
        print(ls_data)

        ### merge all data into a single array
        '''
        data = []
        reference:
            code: [value]            
        '''
        ls_input = []
        dict_reference = {}
        for method_id in self.ls_method_id:
            dict_reference[method_id] = {
                "ls_value": [],
                "method_postprocess": "",
                "index_choose": -1,
                "s3_path": ""
            }

        
        """
        ls_data format:
        {
            "input_data":[
                {
                    "filename":"10x-featured-social-media-image-size.png",
                    "s3_key":"daita-client-data/us-east-2:82c188bc-90ab-4d16-bf43-236ed53a264a/prj1_5be2470b86414756b8169d7a78231756/10x-featured-social-media-image-size.png"
                },
                {
                    "filename":"1200px-Image_created_with_a_mobile_phone.png",
                    "s3_key":"daita-client-data/us-east-2:82c188bc-90ab-4d16-bf43-236ed53a264a/prj1_5be2470b86414756b8169d7a78231756/1200px-Image_created_with_a_mobile_phone.png"
                }
            ],
            "reference":{
                "PRE-008":[
                    [
                    1.5019473227035838,
                    1.2918198043762985
                    ],
                    "sorted"
                ],
                "PRE-002":[
                    [
                    0.03709462515358621,
                    0.09083456000619683
                    ],
                    "median"
                ]
            }
        },
        """
        for data in ls_data:
            input_data = data["input_data"]
            reference: dict = data["reference"]
            ls_input += [x["s3_key"] for x in input_data]
            for item, value in reference.items():
                if dict_reference.get(item, None) is not None:
                    dict_reference[item]["ls_value"] += value[0]
                    dict_reference[item]["method_postprocess"] = value[1]
                else:
                    continue
        
        print("ls_input fetch data: ", ls_input)
        print("dict reference fetch data: ", dict_reference)

        ### get the index of choosen reference image and get the s3 path follow the index
        for method_id, value in dict_reference.items():
            method_postprocess = value["method_postprocess"]
            ls_calculate_value = value["ls_value"]
            index = DICT_POSTPROCESS_METHOD[method_postprocess](ls_calculate_value)
            value["index_choose"] = index
            value["s3_path"] = ls_input[index]
        print("dict reference after choose index: ", dict_reference)

        ### update to DB info with project_id and method_id
        self.reference_info_model.create_reference_info(self.project_id, dict_reference, task_id=self.task_id)

        ### update task finish status
        self.task_model.update_status(self.task_id, self.identity_id, VALUE_TASK_FINISH)

        ### update reference images to project table
        if len(self.project_name)>0:
            dict_ref_save = {}
            for method in self.ls_method_choose:
                if method in dict_reference.keys():
                    dict_ref_save[method] = dict_reference[method]["s3_path"]
            ## save dict_ref_save to project
            self.project_model.update_project_reference_images(self.identity_id, self.project_name, self.ls_method_choose)

                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={},
            is_in_stepfunction=True
        )
       
def lambda_handler(event, context):

    return MergeResultClass().handle(event, context)

    