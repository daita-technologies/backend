import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *
from utils import from_dynamodb_to_json

from system_parameter_store import SystemParameterStore
from lambda_base_class import LambdaBaseClass
from models.task_model import TaskModel


class TaskDashboardClass(LambdaBaseClass):
    def __init__(self) -> None:
        super().__init__()
        self.client_events = boto3.client("events")
        self.const = SystemParameterStore()
        self.table_generateTask = TaskModel(
            os.environ["TableGenerateTaskName"],
            os.environ["INDEX_TASK_PROJECTID_TASKID"],
        )
        self.table_dataflowTask = TaskModel(
            os.environ["TableDataFlowTaskName"],
            os.environ["INDEX_TASK_PROJECTID_TASKID"],
        )
        self.table_healthcheckTask = TaskModel(
            os.environ["TableHealthCheckTasksName"],
            os.environ["INDEX_TASK_PROJECTID_TASKID"],
        )
        self.table_referenceImageTask = TaskModel(
            os.environ["TableReferenceImageName"],
            os.environ["INDEX_TASK_PROJECTID_TASKID"],
        )

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.id_token = body[KEY_NAME_ID_TOKEN]
        self.filter = body[KEY_NAME_FILTER]
        self.pagination = body[KEY_NAME_PAGINATION]
        self.size_ls_item = body[KEY_SIZE_LS_ITEM_QUERY]

        self.filter_prj_id = self.filter.get(KEY_NAME_PROJECT_ID, "")
        self.filter_ls_process_type = self.filter[KEY_NAME_PROCESS_TYPE]
        self.filter_ls_status = self.filter["status_query"]

        self.pag_page_token = self.pagination["page_token"]

    def _check_input_value(self):
        self.size_ls_item = min(100, self.size_ls_item)
        for process_type in self.filter_ls_process_type:
            if process_type not in VALUE_LS_PROCESS_TYPE:
                raise Exception(
                    MESS_PROCESS_TYPE_IS_INVALID.format(self.filter_process_type)
                )
        return

    def _map_process_type_w_table(self, process_type):
        if process_type in [VALUE_PROCESS_TYPE_AUGMENT, VALUE_PROCESS_TYPE_PREPROCESS]:
            return self.table_generateTask
        elif process_type in [VALUE_PROCESS_TYPE_DOWNLOAD, VALUE_PROCESS_TYPE_UPLOAD]:
            return self.table_dataflowTask
        elif process_type == VALUE_PROCESS_TYPE_HEALTHCHECK:
            return self.table_healthcheckTask
        elif process_type == VALUE_PROCESS_TYPE_REFERENCE_IM:
            return self.table_referenceImageTask
        else:
            return None

    def _process_get_task(self, identity_id):
        task_info_dict = {}
        if len(self.filter_ls_process_type) == 0:
            self.filter_ls_process_type = VALUE_LS_PROCESS_TYPE

        for process_type in self.filter_ls_process_type:
            table = self._map_process_type_w_table(process_type)
            print(f"Process for process_type: {process_type}")
            ls_task, ls_page_token = table.get_tasks_w(
                identity_id,
                self.filter_prj_id,
                self.filter_ls_status,
                process_type,
                self.pag_page_token,
                self.size_ls_item,
            )
            ls_task = [from_dynamodb_to_json(item) for item in ls_task]
            task_info_dict[process_type] = {
                "ls_task": ls_task,
                "ls_page_token": ls_page_token,
            }
            ls_page_token = []

        return task_info_dict

    def handle(self, event, context):
        ###handle
        ### parse body
        self.parser(event)

        ### check identity
        identity_id = self.get_identity(self.id_token)

        ### process_get_task
        task_info = self._process_get_task(identity_id)

        return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data=task_info,
        )


@error_response
def lambda_handler(event, context):

    return TaskDashboardClass().handle(event, context)
