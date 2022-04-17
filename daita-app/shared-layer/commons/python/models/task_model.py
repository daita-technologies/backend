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

    def _query_task(self, identity_id, filter_exp, pag_page_token, limit_size, projection_str="", att_name = {}):
        if pag_page_token is None:
            ls_page_token = []
            ### get all task with paginator
            response = self.table.query (
                        KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                        FilterExpression=filter_exp,
                        Limit = limit_size,
                        ProjectionExpression= projection_str,
                        ExpressionAttributeNames = att_name                        
                    )
            do_continue = response.get('LastEvaluatedKey')
            return_ls_items = response.get('Items', [])

            while do_continue:
                ls_page_token.append(do_continue)
                response = self.table.query (
                        KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                        FilterExpression=filter_exp,
                        Limit = limit_size,
                        ExclusiveStartKey = do_continue,
                        ProjectionExpression = projection_str,
                        ExpressionAttributeNames = att_name
                    )
                do_continue = response.get('LastEvaluatedKey')
            return (return_ls_items, ls_page_token)
        else:
            response = self.table.query (
                        KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                        FilterExpression=filter_exp,
                        Limit = limit_size,
                        ExclusiveStartKey = pag_page_token,
                        ProjectionExpression = projection_str,
                        ExpressionAttributeNames = att_name
                    )
            return (response.get('Items', []), [])

    def get_tasks_w(self, identity_id, filter_prj_id, filter_ls_status, filter_process_type, pag_page_token, limit_size):
        filterExpression = Attr(self.FIELD_PROCESS_TYPE).eq(filter_process_type)
        if len(filter_prj_id) == 0:
            filterExpression = filterExpression & Attr(self.FIELD_PROJECT_ID).exists()
        else:
            filterExpression = filterExpression & Attr(self.FIELD_PROJECT_ID).eq(filter_prj_id)
        
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
        ls_task, ls_page_token = self._query_task(identity_id, filterExpression, pag_page_token, limit_size, projecttion_str, attr_name)

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
                        '#s' : self.FIELD_STATUS,
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



    


            