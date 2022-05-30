import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *
import json

from botocore.paginate import TokenEncoder
encoder = TokenEncoder()


class TaskModel():  

    FIELD_IDENTITY_ID = "identity_id"
    FIELD_PROJECT_ID = "project_id"
    FIELD_STATUS = "status"    
    FIELD_PROCESS_TYPE = "process_type"
    FIELD_CREATE_TIME = "created_time"  
    FIELD_TASK_ID = "task_id"
    FIELD_UPDATED_TIME = "updated_time"

    ### field for generation task
    FIELD_NUM_GENS_IMAGE = "number_gen_images"
    FIELD_NUM_FINISHED = "number_finished"    

    ### field for reference image
    FIELD_LS_METHOD_ID = "ls_method_id"
    FIELD_EXECUTION_SM_ID = "execution_id"
    FIELD_PROJECT_NAME = "project_name"
    FIELD_LS_METHOD_FE_CHOOSE = "ls_method_choose"

    ### fields for download
    FIELD_DOWNLOAD_PRESIGN_URL = "presign_url"


    def __init__(self, table_name, index_task_projectid_name=None) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 
        self.table_name = table_name
        self.index_name = index_task_projectid_name
        self.paginator = boto3.client('dynamodb').get_paginator('query')

    def _paginate_query_w_option(self, key_condition_exp, filter_exp, limit_size, projection_str, attr_name, attr_value,
                         ex_start_key=None, index_table = None, text_print = "response from query"):
                       
        
        if ex_start_key is not None: 
            ### just keep the primary key in key input
            start_key = {
                self.FIELD_IDENTITY_ID: ex_start_key[self.FIELD_IDENTITY_ID],
                self.FIELD_TASK_ID: ex_start_key[self.FIELD_TASK_ID],
                self.FIELD_PROJECT_ID: ex_start_key[self.FIELD_PROJECT_ID]
            }
            
            # if query all prjs, we must remove prj_id in start key
            if attr_value.get(":prid", None) is None:
                start_key.pop(self.FIELD_PROJECT_ID, None)
                
            print(f"Start key before encode: {start_key}")
            ex_start_key = encoder.encode({"ExclusiveStartKey": start_key})
        
        dict_argv = {
            "KeyConditionExpression": key_condition_exp,
            "FilterExpression": filter_exp,
            "Limit": limit_size,
            "ProjectionExpression": projection_str,
            "ExpressionAttributeNames": attr_name,
            "ExpressionAttributeValues": attr_value,
            "ScanIndexForward": False,
            "IndexName": index_table,
            "TableName": self.table_name,
            "PaginationConfig":{
                                    'MaxItems': limit_size,
                                    'PageSize': limit_size,
                                    'StartingToken': ex_start_key
                                }
        }
        if index_table is None:
            dict_argv.pop("IndexName", None)
            
        print(f"Dict_argv when call paginate: {dict_argv}")

        responseIterator = self.paginator.paginate(**dict_argv)
        
        print("has responseIterator")
        if responseIterator is None:
            print("response interator is NONE")
            
        print("---------------------------")
        
        ls_items = []
        next_token = None
        for response in responseIterator:
            # print("reponse: ", response)
            items = response.get('Items', [])
            count = response.get("Count", 0)
            last_key = response.get("LastEvaluatedKey", None)
            
            ls_items += items
           
            print(f"count: {count} len_of_items: {len(items)}  last_key: {last_key}")
            if count>len(items):
                next_token = items[-1]
            elif count == len(items) and last_key and count>0:
                next_token = items[-1]
                
        print(f"ls_items: \n {ls_items} \n next_token: {next_token}")
        
        return ls_items, next_token

    def _query_task(self, pag_page_token, key_condition_exp, filter_exp, limit_size, projection_str="", attr_name={}, attr_value = {},
                    index_table=None, text_print="response from query"):
        return_ls_items = []
        if pag_page_token is None:
            print("in page token none")
            ls_page_token = []
            ### get all task with paginator
            return_ls_items, do_continue = self._paginate_query_w_option(key_condition_exp, filter_exp, limit_size, projection_str, attr_name, attr_value,
                                            ex_start_key=None, index_table=index_table, text_print="response from query pagetoken none FIRST") 
            
            
            while do_continue: 
                ls_page_token.append(do_continue)
                _, do_continue = self._paginate_query_w_option(key_condition_exp, filter_exp, limit_size, projection_str, attr_name, attr_value,
                                                ex_start_key=do_continue, index_table=index_table, text_print="response from query in WHILE LOOP") 
                                                
            return (return_ls_items, ls_page_token)
        else:
            print("Page not none: ", pag_page_token)
            return_ls_items, do_continue = self._paginate_query_w_option(key_condition_exp, filter_exp, limit_size, projection_str, attr_name, attr_value,
                                            ex_start_key=pag_page_token, index_table=index_table, text_print="response from query")
            
            return (return_ls_items, [])

    def get_tasks_w(self, identity_id, filter_prj_id, filter_ls_status, filter_process_type, pag_page_token, limit_size):
        attr_name = {
            "#sta": self.FIELD_STATUS,
            "#prid": self.FIELD_PROJECT_ID,
            "#iden_id": self.FIELD_IDENTITY_ID,
            "#proc_type": self.FIELD_PROCESS_TYPE
        }
        attr_value = {
            ":prid": {"S": filter_prj_id},
            ":iden_id": {"S": identity_id},
            ":proc_type": {"S": filter_process_type}
        }
        
        filterExpression = f"#proc_type = :proc_type "
        if len(filter_prj_id) == 0:
            filterExpression = f"{filterExpression} AND attribute_exists(#prid) "
            key_condition_exp = f"#iden_id = :iden_id"
            index_table = None
            attr_value.pop(":prid", None)
            is_get_all_prj = True
        else:
            key_condition_exp = f"#prid = :prid"
            index_table = self.index_name
            attr_name.pop("#iden_id", None)
            attr_value.pop(":iden_id", None)
            is_get_all_prj = False
            
        print("============================")
        
        if len(filter_ls_status) == 0:
            filterExpression = f"{filterExpression} AND attribute_exists(#sta)"
        else:
            filter_status_exp = ""
            for filter_status in filter_ls_status:
                if filter_status in [VALUE_TASK_ERROR, VALUE_TASK_FINISH]:
                    if filter_status == VALUE_TASK_ERROR:
                        attr_value[":val_ta_err"] = {"S": VALUE_TASK_ERROR}
                        filter = f"#sta = :val_ta_err "
                    else:
                        attr_value[":val_ta_finish"] = {"S": VALUE_TASK_FINISH}
                        filter = f"#sta = :val_ta_finish "

                    if filter_status is None:
                        filter_status_exp = filter
                    else:
                        if len(filter_status_exp)>0:
                            filter_status_exp = f" {filter_status_exp} OR {filter} "
                        else:
                            filter_status_exp = f"{filter}"
                else:
                    attr_value[":val_ta_err"] = {"S": VALUE_TASK_ERROR}
                    attr_value[":val_ta_finish"] = {"S": VALUE_TASK_FINISH}
                    filter = f"#sta <> :val_ta_err AND #sta <> :val_ta_finish"
                    if filter_status_exp is None:
                        filter_status_exp = filter
                    else:
                        if len(filter_status_exp)>0:
                            filter_status_exp = f" {filter_status_exp} OR ( {filter} )"
                        else:
                            filter_status_exp = f"{filter}"                        

            filterExpression = f"{filterExpression} AND ({filter_status_exp})"

        projecttion_str = f'{self.FIELD_IDENTITY_ID}, {self.FIELD_PROCESS_TYPE}, {self.FIELD_TASK_ID}, {self.FIELD_PROJECT_ID}, #sta, {self.FIELD_CREATE_TIME}'
        if filter_process_type in [VALUE_PROCESS_TYPE_AUGMENT, VALUE_PROCESS_TYPE_PREPROCESS]:
            projecttion_str = f'{projecttion_str}, {self.FIELD_NUM_GENS_IMAGE}, {self.FIELD_NUM_FINISHED}'
        elif filter_process_type == VALUE_PROCESS_TYPE_DOWNLOAD:
            projecttion_str = f'{projecttion_str}, {self.FIELD_DOWNLOAD_PRESIGN_URL}'
        else:
            pass
        
        print(f"Before query: \n index_name: {index_table}. \n key_condition_exp: {key_condition_exp}")
        ls_task, ls_page_token = self._query_task(pag_page_token, key_condition_exp, filterExpression, limit_size, projection_str=projecttion_str, 
                                                    attr_name = attr_name, attr_value = attr_value,
                                                  index_table = index_table)

        return ls_task, ls_page_token

    def update_status(self, task_id, identity_id, status):
        response = self.table.update_item(
            Key={
                self.FIELD_TASK_ID: task_id,
                self.FIELD_IDENTITY_ID: identity_id
            },
            UpdateExpression="SET #s=:s, #updated_time=:updated_time",
            ExpressionAttributeValues={
                ':s': status,
                ':updated_time': convert_current_date_to_iso8601()
            },
            ExpressionAttributeNames={
                '#s': self.FIELD_STATUS,
                '#updated_time': self.FIELD_UPDATED_TIME,
            }
        )
        
        return response

    def update_attribute(self, task_id, identity_id, ls_update):
        """
        Update the list of attribute (not contains key) with value

        params:
        - ls_udpate: List[(<Field_name>, <value>)]
        """
        exprAttValue = {
            ":up_ti": convert_current_date_to_iso8601()
        }
        exprAttName = {
            "#up_ti": self.FIELD_UPDATED_TIME
        }
        updateExpr = "SET #up_ti = :up_ti, "
        for field_name, value in ls_update:
            exprAttValue[f":{field_name}"] = value
            exprAttName[f"#{field_name}"] = field_name
            updateExpr += f" #{field_name}=:{field_name}, "  
              
        updateExpr = updateExpr[:-2]

        print("update expression: \n", updateExpr)
        print("exprAttValue: \n", exprAttValue)
        print("exprAttName: \n", exprAttName)

        response = self.table.update_item(
                    Key={
                            self.FIELD_TASK_ID: task_id,
                            self.FIELD_IDENTITY_ID: identity_id
                        },
                    UpdateExpression = updateExpr,
                    ExpressionAttributeValues = exprAttValue,
                    ExpressionAttributeNames = exprAttName
                )
        
        return response


    def update_generate_progress(self, task_id, identity_id, num_finish, status):
        response = self.table.update_item(
                    Key = {
                            self.FIELD_TASK_ID: task_id,
                            self.FIELD_IDENTITY_ID: identity_id
                        },
                    UpdateExpression = "SET #s=:s, #num_finished=:num_finished, #updated_time=:updated_time",
                    ExpressionAttributeValues = {
                        ':s': status,
                        ':num_finished': num_finish,
                        ':updated_time': convert_current_date_to_iso8601()
                    },
                    ExpressionAttributeNames = {
                                                '#s' : self.FIELD_STATUS,
                                                '#updated_time': self.FIELD_UPDATED_TIME,
                                                '#num_finished': 'number_finished'
                                            }
                )

        return response

    def create_task_reference_image(self, identity_id, project_id, project_name, ls_method_id, ls_method_client_choose):
        process_type = VALUE_PROCESS_TYPE_REFERENCE_IM
        task_id = create_task_id_w_created_time()
        dict_info = {
            self.FIELD_IDENTITY_ID: identity_id,
            self.FIELD_TASK_ID: task_id,
            self.FIELD_STATUS: VALUE_TASK_RUNNING,                
            self.FIELD_PROJECT_ID: project_id,
            self.FIELD_LS_METHOD_ID: ls_method_id,
            self.FIELD_CREATE_TIME: convert_current_date_to_iso8601(),
            self.FIELD_UPDATED_TIME: convert_current_date_to_iso8601(),
            self.FIELD_PROCESS_TYPE: process_type,
            self.FIELD_LS_METHOD_FE_CHOOSE: ls_method_client_choose,
            self.FIELD_PROJECT_NAME: project_name
        }
        self.table.put_item(
            Item = dict_info
        )

        return task_id, process_type

    def get_task_info_w_atribute(self, identity_id, task_id, ls_attribute=[FIELD_TASK_ID, FIELD_STATUS, FIELD_PROCESS_TYPE]):
        a = {
                    self.FIELD_IDENTITY_ID: identity_id,
                    self.FIELD_TASK_ID: task_id                    
                }
        print("key structure: ", a)
        print("self.tablename: ", self.table_name)
        print("key_schema: ", self.table.key_schema)
        response = self.table.get_item(
                Key={
                    self.FIELD_IDENTITY_ID: identity_id,
                    self.FIELD_TASK_ID: task_id                    
                }                
            )
        item = response.get("Item", None)
        if item:
            info = {}
            for attr in ls_attribute:
                info[attr] = item[attr]
        else:
            info = None
        
        return info
        
    
