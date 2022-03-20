import boto3
import json
import datetime

from config import *
from response import *
from error_messages import *
from identity_check import *

from system_parameter_store import SystemParameterStore
from models.generate_task_model import GenerateTaskModel
from models.project_model import ProjectModel, ProjectItem


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

def check_generate_times_limitation(identity_id, project_name, type_method):
    project_model = ProjectModel()
    project_rec = project_model.get_project_info(identity_id, project_name)
    times_generated = int(project_rec.get_value_w_default(ProjectItem.FIELD_TIMES_AUGMENT, 0))
    times_preprocess = int(project_rec.get_value_w_default(ProjectItem.FIELD_TIMES_PREPRO, 0))
    s3_prefix = project_rec.__dict__[ProjectItem.FIELD_S3_PREFIX]
    const = SystemParameterStore()

    if type_method == VALUE_TYPE_METHOD_AUGMENT: 
        if times_generated >= int(const.limit_augment_times):
            raise Exception(MESS_REACH_LIMIT_AUGMENT.format(const.limit_augment_times))    
    elif type_method == VALUE_TYPE_METHOD_PREPROCESS:
        if times_preprocess >= int(const.limit_prepro_times):
            raise Exception(MESS_REACH_LIMIT_PREPROCESS.format(const.limit_prepro_times))

    return times_generated, times_preprocess, s3_prefix

def put_event_bus(detail_pass_para):
    client = boto3.client('events')
    response = client.put_events(
                    Entries=[
                        {
                            'Source': 'source.events',
                            'DetailType': 'lambda.event',
                            'Detail': json.dumps(detail_pass_para),
                            'EventBusName': os.environ["EVENT_BUS_NAME"]
                        },
                    ]
                )
    entries = response["Entries"]

    return entries[0]["EventId"]

@error_response
def lambda_handler(event, context):
    ### parse parameter from body input   
    try:    
        body = json.loads(event['body'])
        print("Body: \n", body)

        id_token = body[KEY_NAME_ID_TOKEN]
        project_id = body[KEY_NAME_PROJECT_ID]
        project_name = body[KEY_NAME_PROJECT_NAME]
        ls_methods_id = body[KEY_NAME_LS_METHOD_ID]
        data_type = body.get(KEY_NAME_DATA_TYPE, 'ORIGINAL')  # type is one of ORIGINAL or PREPROCESS, default is original        
        num_aug_per_imgs = min(MAX_NUMBER_GEN_PER_IMAGES, body.get(KEY_NAME_NUM_AUG_P_IMG, 1)) # default is 1
        data_number = body[KEY_NAME_DATA_NUMBER]  # array of number data in train/val/test  [100, 19, 1]
    except Exception as e:
        raise Exception(MESS_INVALID_JSON_INPUT) from e

    ### check identity
    identity_id = aws_get_identity_id(id_token)
    
    ### check input value
    check_input_value(data_number, ls_methods_id)

    ### check running task
    generate_task_model = GenerateTaskModel()
    check_running_task(generate_task_model, identity_id, project_id)

    
    ### get type of process
    type_method = get_type_method(ls_methods_id)

    ### check generate times limitation and get times of preprocess and augment
    times_augment, times_preprocess, s3_prefix = check_generate_times_limitation(identity_id, project_name, type_method)   

    ### push event to eventbridge
    detail_pass_para = {
        KEY_NAME_PROJECT_ID: project_id,
        KEY_NAME_PROJECT_NAME: project_name,
        KEY_NAME_LS_METHOD_ID: ls_methods_id,
        KEY_NAME_DATA_TYPE: data_type,
        KEY_NAME_DATA_NUMBER: data_number,
        KEY_NAME_S3_PREFIX: s3_prefix,
        KEY_NAME_TIMES_AUGMENT: times_augment+1,
        KEY_NAME_TIMES_PREPROCESS: times_preprocess+1
    }
    event_id = put_event_bus(detail_pass_para) 
            
    return generate_response(
        message="OK",
        status_code=HTTPStatus.OK,
        data={
            KEY_NAME_TASK_ID: event_id,
            KEY_NAME_TIMES_AUGMENT: (times_augment+1),
            KEY_NAME_TIMES_PREPROCESS: (times_preprocess+1)
        },
    )

    