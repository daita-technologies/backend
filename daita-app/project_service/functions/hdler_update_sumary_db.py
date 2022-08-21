import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.data_model import DataModel, DataItem
from models.task_model import TaskModel
from utils import get_bucket_key_from_s3_uri, split_ls_into_batch


class UpdateSummaryDBClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.client_events = boto3.client('events')    
        self.const = SystemParameterStore()  
        self.s3 = boto3.client('s3')
        self.task_model = TaskModel(os.environ["TABLE_REFERENCE_IMAGE_TASK"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.execution_id = body["id"]
        body = body["detail"]
        self.identity_id = body[KEY_NAME_IDENTITY_ID]
        self.project_id = body[KEY_NAME_PROJECT_ID]
        self.task_id   = body[KEY_NAME_TASK_ID]   
        self.ls_method_id = body[KEY_NAME_LS_METHOD_ID]     

    def _check_input_value(self):
        pass

    def handle(self, event, context):
        
        ### parse body
        self.parser(event)   
        
        ### update task execution arn
        self.task_model.update_attribute(self.task_id, self.identity_id, 
                                            [(TaskModel.FIELD_EXECUTION_SM_ID, self.execution_id)])

        ### get data DB corresponding
        data_table_name = os.environ["TABLE_DATA_ORIGINAL"]                 
        self.data_model = DataModel(data_table_name)
            
        ### get all data from original to calculate reference image
        ls_info = self.data_model.get_all_data_in_project(self.project_id)

        ### split into batch
        batch_size = int(self.const.get_param(os.environ["BATCHSIZE_REF_IMG"]))
        print("Batch size value: ", batch_size)
        ls_batchs = split_ls_into_batch(ls_info, batch_size=batch_size)
        print("ls_batchs: ", ls_batchs)

        if len(ls_info)>0:
            bucket, folder = get_bucket_key_from_s3_uri(ls_info[0][DataItem.FIELD_S3_KEY])
            folder = "/".join(folder.split("/")[:-1])
            s3_key_path = os.path.join(folder, f"reference_image_step_output/{self.task_id}/RI_getdata.json")
            self.s3.put_object(
                Body=json.dumps(ls_batchs),
                Bucket= bucket,
                Key= s3_key_path
            )            
        else:
            bucket = None
            s3_key_path = None
                
        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={
                    "bucket": bucket,
                    "s3_key_path": s3_key_path,
                    "ls_length_batch": list(range(len(ls_batchs)))
                },
            is_in_stepfunction=True
        )
       
def lambda_handler(event, context):

    return UpdateSummaryDBClass().handle(event, context)

    