import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *


# class GenerateTaskItem():
#     FIELD_IDENTITY_ID = "identity_id"
#     FIELD_PROJECT_ID = "project_id"
#     FIELD_STATUS = "status"
#     FIELD_NUM_VALUE = "num_value"
#     FIELD_TASK_ID = "task_id"
#     FIELD_TYPE_METHOD = "type_method"
#     FIELD_UPDATE_TIME = "updated_time"
#     FIELD_NUMBER_FINISHED = "number_finished"
#     FIELD_PROJECT_ID = "project_id"
#     FIELD_NUM_GEN_IMAGES = "number_gen_images"
#     FIELD_CREATE_TIME = "created_time"

#     REQUEST_TYPE_ALL            = "all"
#     REQUEST_TYPE_TASK_PROGRESS  = "task_progress"

#     def __init__(self) -> None:
#         self.identity_id        = ""
#         self.task_id            = ""
#         self.status             = ""
#         self.type_method        = ""
#         self.number_finished    = 0
#         self.number_gen_images  = 0
#         self.project_id         = ""
#         self.create_time        = convert_current_date_to_iso8601()
#         self.updated_time       = convert_current_date_to_iso8601()


#     def to_dict(self, request = REQUEST_TYPE_ALL):
#         print(self.__dict__)
#         if request == self.REQUEST_TYPE_TASK_PROGRESS:
#             dict_info = {
#                 self.FIELD_IDENTITY_ID: self.identity_id,
#                 self.FIELD_TASK_ID: self.task_id,
#                 self.FIELD_STATUS: self.status,
#                 self.FIELD_PROCESS_TYPE: self.process_type,
#                 self.FIELD_NUMBER_FINISHED: self.number_finished,
#                 self.FIELD_NUM_GEN_IMAGES: self.number_gen_images,
#                 self.FIELD_PROJECT_ID: self.project_id
#             }
#         else:
#             dict_info = {
#                 self.FIELD_IDENTITY_ID: self.identity_id,
#                 self.FIELD_TASK_ID: self.task_id,
#                 self.FIELD_STATUS: self.status,
#                 self.FIELD_TYPE_METHOD: self.type_method,
#                 self.FIELD_NUMBER_FINISHED: self.number_finished,
#                 self.FIELD_NUM_GEN_IMAGES: self.number_gen_images,
#                 self.FIELD_PROJECT_ID: self.project_id,
#                 self.FIELD_CREATE_TIME: self.create_time,
#                 self.FIELD_UPDATE_TIME: self.updated_time
#             }
#         return dict_info

#     def from_db_item(self, item_info):
#         if item_info is None:
#             return None
#         else:
#             self.identity_id        = item_info.get(self.FIELD_IDENTITY_ID)
#             self.task_id            = item_info.get(self.FIELD_TASK_ID)
#             self.updated_time       = item_info.get(self.FIELD_UPDATE_TIME)
#             self.status             = item_info.get(self.FIELD_STATUS)
#             self.process_type       = item_info.get(self.FIELD_TYPE_METHOD)
#             self.number_finished    = int(item_info.get(self.FIELD_NUMBER_FINISHED))
#             self.number_gen_images  = int(item_info.get(self.FIELD_NUM_GEN_IMAGES))
#             self.project_id         = item_info.get(self.FIELD_PROJECT_ID)

#             return self   

#     @classmethod
#     def create_new_generate_task(cls, identity_id, project_id, type_method):
#         object = cls()
#         object.task_id = create_unique_id()
#         object.type_method = type_method
#         object.status = VALUE_GENERATE_TASK_STATUS_PENDING
#         object.identity_id = identity_id
#         object.project_id = project_id
        
#         return object



class TaskModel():  

    FIELD_IDENTITY_ID = "identity_id"
    FIELD_PROJECT_ID = "project_id"
    FIELD_STATUS = "status"    
    FIELD_PROCESS_TYPE = "process_type"
    FIELD_CREATE_TIME = "created_time"  


    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name)        
   
    def query_running_tasks(self, identity_id, project_id):
        response = self.table.query (
                KeyConditionExpression=Key(GenerateTaskItem.FIELD_IDENTITY_ID).eq(identity_id),
                FilterExpression=Attr(GenerateTaskItem.FIELD_PROJECT_ID).eq(project_id) & 
                                Attr(GenerateTaskItem.FIELD_STATUS).ne(VALUE_GENERATE_TASK_STATUS_FINISH) & 
                                Attr(GenerateTaskItem.FIELD_STATUS).ne(VALUE_GENERATE_TASK_STATUS_ERROR)
            )
        return response.get("Items", []) 

    def _query_task(self, identity_id, filter_exp, pag_page_token, limit_size):
        if pag_page_token is None:
            ls_page_token = []
            ### get all task with paginator
            response = self.table.query (
                        KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                        FilterExpression=filter_exp,
                        Limit = limit_size                        
                    )
            do_continue = response.get('LastEvaluatedKey')
            return_ls_items = response.get('Items', [])

            while do_continue:
                ls_page_token.append(do_continue)
                response = self.table.query (
                        KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                        FilterExpression=filter_exp,
                        Limit = limit_size,
                        ExclusiveStartKey = do_continue
                    )
                do_continue = response.get('LastEvaluatedKey')
            return (return_ls_items, ls_page_token)
        else:
            response = self.table.query (
                        KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                        FilterExpression=filter_exp,
                        Limit = limit_size,
                        ExclusiveStartKey = pag_page_token
                    )
            return (response.get('Items', []), [])

    def get_tasks_w(self, identity_id, filter_prj_id, filter_status, filter_process_type, pag_page_token, limit_size):
        filterExpression = Attr(self.FIELD_PROCESS_TYPE).eq(filter_process_type)
        if len(filter_prj_id) == 0:
            filterExpression = filterExpression & Attr(self.FIELD_PROJECT_ID).exists()
        else:
            filterExpression = filterExpression & Attr(self.FIELD_PROJECT_ID).eq(filter_prj_id)
        
        if filter_status == "ALL":
            filterExpression = filterExpression & Attr(self.FIELD_STATUS).exists()
        else:
            filterExpression = filterExpression & Attr(self.FIELD_STATUS).eq(filter_status)

        ls_task, ls_page_token = self._query_task(identity_id, filterExpression, pag_page_token, limit_size)

        return ls_task, ls_page_token



            