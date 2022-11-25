import requests
import time
from config import *
from response import *
from utils import *
from identity_check import *
from lambda_base_class import LambdaBaseClass


class GetReferenceImageClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()

    @LambdaBaseClass.parse_body
    def parser(self, body):
        pass
        # self.process_type = body['process_type']
        # self.is_retry = body['is_retry']

        
    def _check_input_value(self): 
        pass

    def handle(self, event, context):
        
        if 'process_type' in event and event['process_type'] != 'PREPROCESS':
            event['is_retry'] = False
            return event

        if bool(event['reference_images']):
            event['is_retry'] = False
            
        print("event start: \n", event)

        if not 'reference_image_task_id' in event:
            input_data = {
                'id_token': event['id_token'],
                'project_id': event['project_id'],
                'ls_method_client_choose': [],
                'project_name': event['project_name']
            }

            response = self.invoke_lambda_func(self.env.FUNC_RI_CALCULATION, input_data)

            print("response calculation: ", response)

            if response["statusCode"] == 200:
                data = json.loads(response["body"])["data"]
                event['reference_image_task_id'] = data['task_id']
                print(f"Logging Debug :{data}")

        start = time.time()
        while time.time() - start <= 120:
            json_data = {
                'id_token': event['id_token'],
                'task_id': event['reference_image_task_id'],
            }
            reponseStatusRefImage = self.invoke_lambda_func(self.env.FUNC_RI_STATUS, json_data)
            print("reponseStatusRefImage: \n", reponseStatusRefImage)
            
            data = json.loads(reponseStatusRefImage["body"])["data"]
            
            if data['status'] == 'FINISH':
                json_data_info={
                    'project_id': event['project_id'],
                    'id_token': event['id_token'],
                }
                reponseInfoRefImage = self.invoke_lambda_func(self.env.FUNC_RI_INFO, json_data_info)
                print("reponseInfoRefImage: \n", reponseInfoRefImage)
                
                info = json.loads(reponseInfoRefImage["body"])["data"] 
                for it in info:
                    event['reference_images'][it['method_id']
                                            ] = "s3://{}".format(it['image_s3_path'])
                    event['is_retry'] = False
                break
            else:
                event['is_retry'] = True
            time.sleep(5)

        return event
        

@error_response
def lambda_handler(event, context):
    return GetReferenceImageClass().handle(event=event,  context=context)
