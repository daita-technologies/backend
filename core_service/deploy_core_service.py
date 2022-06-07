import os
import sys
import time

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(dir_path, ".."))

print(sys.path)

from aws_lambda.project.de_lambda import deploy_lambda
from api_gateway.de_api_project import deploy_api_project
from dynamoDB.de_dynamodb import deploy_dynamoDB

MODE_DB = ""  #'stage_'

GENERAL_SETUP = {
    "MODE": "staging",
    "BUCKET_NAME": "daita-client-data",
    "USER_POOL_ID": "us-east-2_ZbwpnYN4g",
    "IDENTITY_POOL_ID": "us-east-2:fa0b76bc-01fa-4bb8-b7cf-a5000954aafb",
    "CLIENT_ID": "4cpbb5etp3q7grnnrhrc7irjoa",
    "aws_access_key_id": "AKIAVKWNZXMINQ6JTYXY",
    "aws_secret_access_key": "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",
    "DOWNLOAD_SERVICE_URL": "3.140.206.255",
    "T_PROJECT": MODE_DB + "projects",
    "T_PROJECT_SUMMARY": MODE_DB + "prj_sum_all",
    "T_PROJECT_DEL": MODE_DB + "projects_save_delete",
    "T_DATA_PREPROCESS": MODE_DB + "data_preprocess",
    "T_DATA_ORI": MODE_DB + "data_original",
    "T_DATA_AUGMENT": MODE_DB + "data_augment",
    "T_INSTANCES": MODE_DB + "ec2",
    "T_EC2_TASK": MODE_DB + "ec2_task",
    "T_TASKS": MODE_DB + "dev-generate-tasks",
    "T_METHODS": MODE_DB + "methods",
    "T_QUOTAS": MODE_DB + "quotas",
    "T_TASK_DOWNLOAD": MODE_DB + "down_tasks",
    "T_CONST": MODE_DB + "consts",
    "T_TRIGGER_SEND_CODE": MODE_DB + "Trigger_send_code",
    "T_USER": MODE_DB + "User",
    "T_EVENT_USER": MODE_DB + "eventUser",
    "T_FEEDBACK": MODE_DB + "feedback",
    "IS_ENABLE_KMS": "False",
}


ls_lambda_val = deploy_lambda(GENERAL_SETUP)
deploy_api_project(ls_lambda_val, GENERAL_SETUP)
deploy_dynamoDB(GENERAL_SETUP)
