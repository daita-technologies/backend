from aws_lambda.utils.utils import add_lambda_info_to_list
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
ROOT = str(PROJECT_DIR.joinpath("code"))+'/'
PACKAGES = PROJECT_DIR.joinpath("packages")

def deploy_lambda_generate(general_info, lambda_service):
    ls_lambda_val = []    

    # get all methods for preprocessing and augmentation
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-generate-list-method',
                                         [ROOT + 'generate_list_method.py', ROOT + 'utils.py',
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_METHODS' : general_info['T_METHODS'],
                                        },
                                        'generate_list_method.lambda_handler',
                                        'staging: get list method for generating')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'generate', 'list_method')

    # generate images with augmentation or preprocessing
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-generate-images',
                                         [ROOT + 'generate_images.py', ROOT + 'utils.py',
                                          PACKAGES,
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_METHODS' : general_info['T_METHODS'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_PROJECT_SUMMARY': general_info['T_PROJECT_SUMMARY'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                            'T_INSTANCES': general_info['T_INSTANCES'],
                                        },
                                        'generate_images.lambda_handler',
                                        'staging: generate images with preprocessing or augmentation methods')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'generate', 'images')

    # get current progress
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-generate-task-progress',
                                         [ROOT + 'generate_task_progress.py', ROOT + 'utils.py', 
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                            'T_PROJECT' : general_info['T_PROJECT']
                                        },
                                        'generate_task_progress.lambda_handler',
                                        'staging: get current progress of task_id')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'generate', 'task_progress')  
    
    return ls_lambda_val




    