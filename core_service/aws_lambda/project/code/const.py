import boto3
import os


db_resource = boto3.resource("dynamodb")
table = db_resource.Table("consts")

MAX_NUM_PRJ_PER_USER = 5
MAX_TIMES_AUGMENT_IMAGES = "limit_times_augment"
MAX_TIMES_PREPROCESS_IMAGES = "limit_times_prepro"

SAMPLE_PROJECT_NAME = "Driving Dataset Sample"  #'prj_sample' #
SAMPLE_PROJECT_DESCRIPTION = (
    "An open-source autonomous driving dataset sample to kick-start."
)

MAX_LENGTH_PROJECT_NAME_INFO = 75

MES_LENGTH_OF_PROJECT_NAME = (
    f"Length of project name must smaller than {MAX_LENGTH_PROJECT_NAME_INFO}."
)
MES_LENGTH_OF_PROJECT_INFO = (
    f"Length of project description must smaller than {MAX_LENGTH_PROJECT_NAME_INFO}."
)
MES_REACH_LIMIT_NUM_PRJ = f"You have reached the threshold of {MAX_NUM_PRJ_PER_USER} custom projects per user."
MES_DUPLICATE_PROJECT_NAME = "{} already exists. Please choose another name."
MES_REACH_LIMIT_AUGMENT = (
    "You have reached the threshold of {} augmentation runs per project."
)
MES_REACH_LIMIT_PREPROCESS = (
    "You have reached the threshold of {} preprocessing runs per project."
)

MES_PROJECT_NOT_FOUND = "Project {} is not found."
MES_PROJECT_ALREADY_EXIST = "Project {} exists, please choose another name."
MES_PROJECT_SAME = "New project name {} must different with current name."


def get_const_db(code):
    response = table.get_item(Key={"code": code, "type": "THRESHOLD"})
    return response.get("Item")["num_value"]
