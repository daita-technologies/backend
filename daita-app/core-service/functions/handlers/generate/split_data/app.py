
from config import *
from response import *
from error_messages import *
from identity_check import *

from models.project_model import ProjectModel, ProjectItem
from lambda_base_class import LambdaBaseClass


class SplitDataClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     
        self.project_model = ProjectModel(os.environ["TABLE_PROJECT"])

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.project_name = body[KEY_NAME_PROJECT_NAME]
        self.data_type = body[KEY_NAME_DATA_TYPE].upper()  # type is one of ORIGINAL or PREPROCESS, default is original
        self.data_number = body[KEY_NAME_DATA_NUMBER]  # array of number data in train/val/test  [100, 19, 1]

    def _check_input_value(self):
        if len(self.data_number)>0:
            if self.data_number[0] == 0:
                raise Exception(MESS_NUMBER_TRAINING)
        for number in self.data_number:
            if number<0:
                raise Exception(MESS_NUMBER_DATA)

        if self.data_type not in LS_ACCEPTABLE_VALUE_GENERATE:
            raise Exception(MESS_DATA_TYPE_INPUT.format(self.data_type, LS_ACCEPTABLE_VALUE_GENERATE))

        return

    def handle(self, event, context):

        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### update information
        self.project_model.update_project_info(identity_id, self.project_name, self.data_type, self.data_number)

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=None,
        )



@error_response
def lambda_handler(event, context):

    return SplitDataClass().handle(event, context)
