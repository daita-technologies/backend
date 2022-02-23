import os
import sys
import time
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, '..'))

print(sys.path)

from aws_lambda.project.de_lambda_project import deploy_lambda_project
from api_gateway.de_api_project import deploy_api_project
from dynamoDB.de_dynamodb import deploy_dynamoDB

MODE_DB = ''    #'stage_'

GENERAL_SETUP = {
    'MODE': 'staging',
    'BUCKET_NAME': 'client-data-test',
    'USER_POOL_ID': 'us-east-2_6Sc8AZij7',
    'IDENTITY_POOL_ID': 'us-east-2:639788f0-a9b0-460d-9f50-23bbe5bc7140',

    'T_PROJECT' : MODE_DB + 'projects',
    'T_PROJECT_SUMMARY' : MODE_DB + 'prj_sum_all',
    'T_PROJECT_DEL': MODE_DB + 'projects_save_delete',

    'T_DATA_PREPROCESS': MODE_DB + 'data_preprocess',
    'T_DATA_ORI': MODE_DB + 'data_original',
    'T_DATA_AUGMENT': MODE_DB + 'data_augment',
    
    'T_INSTANCES': MODE_DB + 'ec2',
    'T_EC2_TASK': MODE_DB + 'ec2_task',

    'T_TASKS' : MODE_DB + 'tasks',
    'T_METHODS' : MODE_DB + 'methods',
    "T_QUOTAS": MODE_DB + "quotas",
    "T_TASK_DOWNLOAD": MODE_DB + "down_tasks",
    "T_CONST": MODE_DB + "consts"
}

ls_lambda_val = deploy_lambda_project(GENERAL_SETUP)
deploy_api_project(ls_lambda_val, GENERAL_SETUP)
deploy_dynamoDB(GENERAL_SETUP)



