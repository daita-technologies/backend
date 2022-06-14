from aws_lambda.utils.utils import add_lambda_info_to_list
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
ROOT = str(PROJECT_DIR.joinpath("code"))+'/'
PACKAGES = PROJECT_DIR.joinpath("packages")


def deploy_lambda_project(general_info, lambda_service):
    ls_lambda_val = []


    # create project
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-create', 
                                        [ROOT + 'project_create.py', ROOT + 'utils.py',
                                        ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'BUCKET_NAME': general_info['BUCKET_NAME'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            "T_QUOTAS": general_info['T_QUOTAS'],
                                        },
                                        'project_create.lambda_handler',
                                        'staging: create new project')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'create')

    # create sample project passenger
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-create-sample', 
                                        [ROOT + 'project_sample.py', ROOT + 'utils.py',
                                        ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'BUCKET_NAME': general_info['BUCKET_NAME'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_PROJECT_SUMMARY' : general_info['T_PROJECT_SUMMARY'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                        },
                                        'project_sample.lambda_handler',
                                        'staging: create new sample project')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'create_sample')

    # create sample project async
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-asy-create-sample', 
                                        [ROOT + 'project_asy_create_sameple.py', ROOT + 'utils.py',
                                        ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'BUCKET_NAME': general_info['BUCKET_NAME'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_PROJECT_SUMMARY' : general_info['T_PROJECT_SUMMARY'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                        },
                                        'project_asy_create_sameple.lambda_handler',
                                        'staging: async create new sample project')

    # delete images in project
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-project-delete-image', 
                                        [ROOT + 'project_delete_images.py', ROOT + 'utils.py',
                                        ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'BUCKET_NAME': general_info['BUCKET_NAME'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_PROJECT_SUMMARY' : general_info['T_PROJECT_SUMMARY'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_DATA_AUGMENT': general_info['T_DATA_AUGMENT'],
                                        },
                                        'project_delete_images.lambda_handler',
                                        'staging: delete images in project')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'delete_images')

    # delete project
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-project-delete', 
                                        [ROOT + 'project_delete_project.py', ROOT + 'utils.py',
                                        ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'BUCKET_NAME': general_info['BUCKET_NAME'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_PROJECT_SUMMARY' : general_info['T_PROJECT_SUMMARY'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_DATA_AUGMENT': general_info['T_DATA_AUGMENT'],    
                                            'T_TASKS' : general_info['T_TASKS'],         
                                            'T_PROJECT_DEL': general_info['T_PROJECT_DEL']                               
                                        },
                                        'project_delete_project.lambda_handler',
                                        'staging: delete project')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'delete')

    # update project info: project_name, description
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-update-info',
                                         [ROOT + 'project_update_info.py', ROOT + 'utils.py',
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_PROJECT_SUMMARY' : general_info['T_PROJECT_SUMMARY'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                        },
                                        'project_update_info.lambda_handler',
                                        'staging: update project info')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'update_info')

    # get project info
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-info',
                                         [ROOT + 'project_info.py', ROOT + 'utils.py',
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_PROJECT_SUMMARY' : general_info['T_PROJECT_SUMMARY'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                        },
                                        'project_info.lambda_handler',
                                        'staging: get project info')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'info')

    # get project list
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-list',
                                         [ROOT + 'project_list.py', ROOT + 'utils.py',
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_PROJECT' : general_info['T_PROJECT']
                                        },
                                        'project_list.lambda_handler',
                                        'staging: get list of project')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'list')

    # get list info: get all project and infor of them
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-list-info',
                                         [ROOT + 'project_list_info.py', ROOT + 'utils.py',
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_PROJECT_SUMMARY' : general_info['T_PROJECT_SUMMARY'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                        },
                                        'project_list_info.lambda_handler',
                                        'staging: get list of project with information detail')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'list_info')



    # check existen of file in S3 when upload image for project
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-upload-check',
                                         [ROOT + 'project_upload_check.py', ROOT + 'utils.py',
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_PROJECT_SUMMARY': general_info['T_PROJECT_SUMMARY'],
                                            'T_PROJECT': general_info['T_PROJECT'],
                                            'T_TASK_DOWNLOAD': general_info['T_TASK_DOWNLOAD'],
                                            'T_CONST': general_info['T_CONST'],
                                        },
                                        'project_upload_check.lambda_handler',
                                        'staging: check existen when uploading')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'upload_check')

    # update info from client after finish uploading to S3
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-upload-update',
                                        [ROOT + 'project_upload_update.py', ROOT + 'utils.py',
                                        ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_PROJECT_SUMMARY': general_info['T_PROJECT_SUMMARY'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_DATA_AUGMENT': general_info['T_DATA_AUGMENT'],
                                            'T_PROJECT': general_info['T_PROJECT'],
                                            'T_TASK_DOWNLOAD': general_info['T_TASK_DOWNLOAD'],
                                            'T_CONST': general_info['T_CONST'],
                                        },
                                        'project_upload_update.lambda_handler',
                                        'staging: update information after uploaded')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'upload_update')


    # create a download task 
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-download-create',
                                        [ROOT + 'project_download_create.py', ROOT + 'utils.py',
                                         PACKAGES,
                                        ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'DOWNLOAD_SERVICE_URL': general_info['DOWNLOAD_SERVICE_URL'],
                                            'T_PROJECT_SUMMARY': general_info['T_PROJECT_SUMMARY'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_DATA_AUGMENT': general_info['T_DATA_AUGMENT'],
                                            'T_PROJECT': general_info['T_PROJECT'],
                                            'T_TASK_DOWNLOAD': general_info['T_TASK_DOWNLOAD'],
                                            'T_CONST': general_info['T_CONST'],
                                        },
                                        'project_download_create.lambda_handler',
                                        'staging: create a download task')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'download_create')

    # get progress of downloading task 
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-download-update',
                                        [ROOT + 'project_download_update.py', ROOT + 'utils.py',
                                        ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_PROJECT_SUMMARY': general_info['T_PROJECT_SUMMARY'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_DATA_AUGMENT': general_info['T_DATA_AUGMENT'],
                                            'T_PROJECT': general_info['T_PROJECT'],
                                            'T_TASK_DOWNLOAD': general_info['T_TASK_DOWNLOAD'],
                                            'T_CONST': general_info['T_CONST'],
                                        },
                                        'project_download_update.lambda_handler',
                                        'staging: update the progress of download task')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'download_update')

    # get list data s3_key in the DB, client will use it for downloading
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-list-data',
                                         [ROOT + 'project_list_data.py', ROOT + 'utils.py',
                                         ROOT + 'const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_DATA_AUGMENT': general_info['T_DATA_AUGMENT'],
                                        },
                                        'project_list_data.lambda_handler',
                                        'staging: get project list data')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'list_data')      

    return ls_lambda_val




    