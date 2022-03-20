import boto3
import json

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from models.generate_task_model import GenerateTaskModel
from models.project_model import ProjectModel


def check_input_value(data_number, ls_methods_id):
    if len(data_number)>0:
        if data_number[0] == 0:
            raise Exception(MESS_NUMBER_TRAINING)        
        for number in data_number:
            if number<0:
                raise Exception(MESS_NUMBER_DATA)
        
    if len(ls_methods_id) == 0:
        raise Exception(MESS_LIST_METHODS_EMPTY)
    return

def check_running_task(generate_task_model: GenerateTaskModel, identity_id, project_id):
    """
    Check any running tasks of this project
    """   
    ls_running_task = generate_task_model.get_running_tasks(identity_id, project_id)    
    if len(ls_running_task) > 0:
        raise Exception(MESS_ERROR_OVER_LIMIT_RUNNING_TASK)

def get_type_method(ls_methods_id):
    type_method = VALUE_TYPE_METHOD_PREPROCESS
    if VALUE_TYPE_METHOD_NAME_AUGMENT in ls_methods_id[0]:
        type_method = VALUE_TYPE_METHOD_AUGMENT
    elif VALUE_TYPE_METHOD_NAME_PREPROCESS in ls_methods_id[0]:
        type_method = VALUE_TYPE_METHOD_PREPROCESS
    else:
        raise Exception(MESS_ERR_INVALID_LIST_METHOD)
    
    return type_method


@error_response
def lambda_handler(event, context):
    ### parse parameter from body input   
    try:    
        body = json.loads(event['body'])
        print("Body: \n", body)

        id_token = body["id_token"]
        project_id = body['project_id']
        project_name = body['project_name']
        ls_methods_id = body['ls_method_id']
        data_type = body.get('data_type', 'ORIGINAL')  # type is one of ORIGINAL or PREPROCESS, default is original        
        num_aug_per_imgs = min(MAX_NUMBER_GEN_PER_IMAGES, body.get('num_aug_p_img', 1)) # default is 1
        data_number = body['data_number']  # array of number data in train/val/test  [100, 19, 1]
    except Exception as e:
        raise Exception(MESS_INVALID_JSON_INPUT) from e

    ### check identity
    try:
        identity_id = aws_get_identity_id(id_token)
    except Exception as e:
        raise Exception(MESS_AUTHEN_FAILED) from e
    
    ### check input value
    check_input_value(data_number, ls_methods_id)

    ### check running task
    generate_task_model = GenerateTaskModel()
    check_running_task(generate_task_model, identity_id, project_id)

    
    ### get type of process
    type_method = get_type_method(ls_methods_id)

    ### check generate times limitation
    # project_model = ProjectModel()
    # project_info = project_model.get_project_info(identity_id, project_name)
    # times_generated = int(infor.get("times_generated", 0))
    # times_preprocess = int(infor.get("times_propr", 0))

    # if type_method == VALUE_TYPE_METHOD_AUGMENT: 
    #     if times_generated>=MAX_TIMES_AUGMENT_IMAGES:
    #         raise Exception(const.MES_REACH_LIMIT_AUGMENT.format(MAX_TIMES_AUGMENT_IMAGES))
    #         this_times_generate = times_generated + 1
            
    #         print('this_times_augment: ', this_times_generate)
            
    #         # update data_type and data_number to project
    #         dydb_update_project_data_type_number(db_resource, identity_id, project_name, data_type, data_number, this_times_generate)
    #     else:
    #         this_times_generate = times_generated
    #         if times_preprocess>=MAX_TIMES_PREPROCESS_IMAGES:
    #             raise Exception(const.MES_REACH_LIMIT_PREPROCESS.format(MAX_TIMES_PREPROCESS_IMAGES))
            
    ### get const
    const = SystemParameterStore()
    print(const.limit_augment_times)

    return generate_response(
        message="OK",
        status_code=HTTPStatus.OK,
        data={"ok": const.limit_augment_times},
    )

    