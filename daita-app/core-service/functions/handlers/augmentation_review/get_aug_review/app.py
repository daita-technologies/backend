import json

from config import *
from response import *
from error_messages import *
from s3_utils import generate_presigned_url

from lambda_base_class import LambdaBaseClass
from system_parameter_store import SystemParameterStore


class GetAugmentationImgReviewClass(LambdaBaseClass):

    def __init__(self) -> None:
        super().__init__()
        self.const = SystemParameterStore() 
        self.json_thumbnail_path = "thumbnails.json"

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.method_id = body[KEY_NAME_METHOD_ID]

    def structure_json_data(self, path, method_id_check):
        with open(path, 'r', encoding='utf-8') as fi:
            data = json.load(fi)

        for method_info in data:
            method_id = method_info["method_id"]

            if method_id != method_id_check:
                continue

            ls_param_name = method_info["ls_params_name"]
            ls_param_value = method_info["ls_params_value"]
            ls_aug_img = method_info["ls_aug_img"]

            method_info["dict_aug_img"] = {}
            # if len(ls_param_name)==1:
            #     for idx, value in enumerate(ls_aug_img):
            #         method_info["dict_aug_img"][str(idx)] = value["aug_review_img"]
            # else:        
            for idx, value in enumerate(ls_aug_img):
                str_key = []
                for param_name_idx in ls_param_name:
                    value_param = value["param_value"][param_name_idx]
                    str_key.append(str(ls_param_value[param_name_idx].index(value_param)))  
                key = '|'.join(str_key)
                method_info["dict_aug_img"][key] = generate_presigned_url(value["aug_review_img"])

            ### generate for ls_param_info
            method_info["ls_param_info"] = {}
            for method, ls_value in ls_param_value.items():
                if isinstance(ls_value[0], bool):
                    type = "boolean"
                    step = ""
                else:
                    type = "number"
                    step = ls_value[1]-ls_value[0]
                method_info["ls_param_info"][method] = {
                    "step": step,
                    "type": type
                }

            method_info.pop("ls_aug_img")
            return method_info
        
        return None

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)       

        ### get task info, if task not exist, raise exception       
        info = self.structure_json_data(self.json_thumbnail_path, self.method_id)

        if info is None:
            raise Exception(MESS_METHOD_DOES_NOT_SUPPORT.format(self.method_id))     
                
        return generate_response(
            message="OK",
            status_code = HTTPStatus.OK,
            data = info,
        )

@error_response
def lambda_handler(event, context):

    return GetAugmentationImgReviewClass().handle(event, context)
