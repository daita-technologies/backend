import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *

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


    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name) 

    def _query_w_option(self, key_condition_exp, filter_exp, limit_size, projection_str, attr_name,
                         ex_start_key=None, index_table = None, text_print = "response from query"):
        
        dict_argv = {
            "KeyConditionExpression": key_condition_exp,
            "FilterExpression": filter_exp,
            "Limit": limit_size,
            "ProjectionExpression": projection_str,
            "ExpressionAttributeNames": attr_name,
            "ScanIndexForward": False,
            "ExclusiveStartKey": ex_start_key,
            "IndexName": index_table
        }
        if ex_start_key is None:
            dict_argv.pop("ExclusiveStartKey", None)
        if index_table is None:
            dict_argv.pop("IndexName", None)

        response = self.table.query(**dict_argv)

        print(f"{text_print}: \n {response}")

        return response

    def _query_task(self, pag_page_token, key_condition_exp, filter_exp, limit_size, projection_str="", attr_name={},
                    index_table=None, text_print="response from query"):
        if pag_page_token is None:
            ls_page_token = []
            ### get all task with paginator
            response = self._query_w_option(key_condition_exp, filter_exp, limit_size, projection_str, attr_name,
                                            ex_start_key=None, index_table=index_table, text_print="response from query")            
            do_continue = response.get('LastEvaluatedKey')
            return_ls_items = response.get('Items', [])

            while do_continue:
                ls_page_token.append(do_continue)
                response = self._query_w_option(key_condition_exp, filter_exp, limit_size, projection_str, attr_name,
                                                ex_start_key=do_continue, index_table=index_table, text_print="response from query")                
                do_continue = response.get('LastEvaluatedKey')
            return (return_ls_items, ls_page_token)
        else:
            response = self._query_w_option(key_condition_exp, filter_exp, limit_size, projection_str, attr_name,
                                            ex_start_key=pag_page_token, index_table=index_table, text_print="response from query")
            
            return (response.get('Items', []), [])

    def get_tasks_w(self, identity_id, filter_prj_id, filter_ls_status, filter_process_type, pag_page_token, limit_size):
        filterExpression = Attr(self.FIELD_PROCESS_TYPE).eq(filter_process_type)
        if len(filter_prj_id) == 0:
            filterExpression = filterExpression & Attr(self.FIELD_PROJECT_ID).exists()
            key_condition_exp = Key(self.FIELD_IDENTITY_ID).eq(identity_id)
            index_table = None
        else:
            key_condition_exp = Key(self.FIELD_PROJECT_ID).eq(filter_prj_id)
            index_table = 
        
        if len(filter_ls_status) == 0:
            filterExpression = filterExpression & Attr(self.FIELD_STATUS).exists()
        else:
            filter_status = None
            for filter_status in filter_ls_status:
                if filter_status in [VALUE_TASK_ERROR, VALUE_TASK_FINISH]:
                    filter = Attr(self.FIELD_STATUS).eq(filter_status)
                    if filter_status is None:
                        filter_status = filter
                    else:
                        filter_status = filter_status | filter
                else:
                    filter = (Attr(self.FIELD_STATUS).ne(VALUE_TASK_ERROR) & Attr(self.FIELD_STATUS).ne(VALUE_TASK_FINISH))
                    if filter_status is None:
                        filter_status = filter
                    else:
                        filter_status = filter_status | filter

            filterExpression = filterExpression & (filter_status)

        projecttion_str = f'{self.FIELD_IDENTITY_ID}, {self.FIELD_PROCESS_TYPE}, {self.FIELD_TASK_ID}, {self.FIELD_PROJECT_ID}, #sta, {self.FIELD_CREATE_TIME}'
        attr_name = {
            "#sta": self.FIELD_STATUS
        }

        ls_task, ls_page_token = self._query_task(pag_page_token, key_condition_exp, filterExpression, limit_size, projecttion_str, attr_name,
                                                  index_table)

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



    


            