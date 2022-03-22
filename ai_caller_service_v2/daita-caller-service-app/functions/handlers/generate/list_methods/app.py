
import json

from config import *
from response import *
from error_messages import *

from lambda_base_class import LambdaBaseClass
from models.method_model import MethodModel, MethodItem

class ListMethodsClass(LambdaBaseClass):

    def __init__(self) -> None:
        super().__init__()
        self.method_model = MethodModel()    

    def _restructure_items_response(self, items: List[MethodItem]):       

        dict_type = {
                KEY_NAME_RES_AUMENTATION: [],
                KEY_NAME_RES_PREPROCESSING: []
            }
        for item in items:
            if VALUE_TYPE_METHOD_NAME_AUGMENT in item.method_id:
                dict_type[KEY_NAME_RES_AUMENTATION].append(item.item_db)
            elif VALUE_TYPE_METHOD_NAME_PREPROCESS in item.method_id:
                dict_type[KEY_NAME_RES_PREPROCESSING].append(item.item_db)
            else:
                self.logger.warning(f"Method id {item[MethodItem.FIELD_METHOD_ID]} with shorten method name not belong to {VALUE_TYPE_METHOD_NAME_AUGMENT}|{VALUE_TYPE_METHOD_NAME_PREPROCESS}")
        
        return dict_type

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")
        self.id_token = body[KEY_NAME_ID_TOKEN]        

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)       

        ### get all methods       
        items = self.method_model.get_all_methods()   
        data_response = self._restructure_items_response(items)    
                
        return generate_response(
            message="OK",
            status_code = HTTPStatus.OK,
            data = data_response,
        )

@error_response
def lambda_handler(event, context):

    return ListMethodsClass().handle(event, context)

    