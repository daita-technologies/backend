import boto3
import botocore
from backend.aws_lambda.lambda_service import AWSLambdaService

def add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, api_resource, api_name):
    # when lambda_uri return will have the version of lambda function, so, when pass to api, we remove it to run the latest version
    # example:   ...../lambda:1  => ...../lambda
    version_function = lambda_uri.split(':')[-1]
    lambda_uri = lambda_uri[:-(len(version_function)+1)]
    ls_lambda_val.append((lambda_uri, lambda_version, api_resource, api_name))

def deploy_lambda_project(general_info):
    lambda_service = AWSLambdaService()
    ls_lambda_val = []

    # create project
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-create', 
                                        [r'backend\aws_lambda\project\code\project_create.py', r'backend\aws_lambda\project\code\utils.py',
                                        r'backend\aws_lambda\project\code\const.py'],
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
                                        [r'backend\aws_lambda\project\code\project_sample.py', r'backend\aws_lambda\project\code\utils.py',
                                        r'backend\aws_lambda\project\code\const.py'],
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
                                        [r'backend\aws_lambda\project\code\project_asy_create_sameple.py', r'backend\aws_lambda\project\code\utils.py',
                                        r'backend\aws_lambda\project\code\const.py'],
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
                                        [r'backend\aws_lambda\project\code\project_delete_images.py', r'backend\aws_lambda\project\code\utils.py',
                                        r'backend\aws_lambda\project\code\const.py'],
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
                                        [r'backend\aws_lambda\project\code\project_delete_project.py', r'backend\aws_lambda\project\code\utils.py',
                                        r'backend\aws_lambda\project\code\const.py'],
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
                                         [r'backend\aws_lambda\project\code\project_update_info.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
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
                                         [r'backend\aws_lambda\project\code\project_info.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
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
                                         [r'backend\aws_lambda\project\code\project_list.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
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
                                         [r'backend\aws_lambda\project\code\project_list_info.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
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
                                         [r'backend\aws_lambda\project\code\project_upload_check.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
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
                                        [r'backend\aws_lambda\project\code\project_upload_update.py', r'backend\aws_lambda\project\code\utils.py',
                                        r'backend\aws_lambda\project\code\const.py'],
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
                                        [r'backend\aws_lambda\project\code\project_download_create.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\packages',
                                        r'backend\aws_lambda\project\code\const.py'],
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
                                        'project_download_create.lambda_handler',
                                        'staging: create a download task')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'project', 'download_create')

    # get progress of downloading task 
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-project-download-update',
                                        [r'backend\aws_lambda\project\code\project_download_update.py', r'backend\aws_lambda\project\code\utils.py',
                                        r'backend\aws_lambda\project\code\const.py'],
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
                                         [r'backend\aws_lambda\project\code\project_list_data.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
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

    # get all methods for preprocessing and augmentation
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-generate-list-method',
                                         [r'backend\aws_lambda\project\code\generate_list_method.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
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
                                         [r'backend\aws_lambda\project\code\generate_images.py', r'backend\aws_lambda\project\code\utils.py', r'backend\aws_lambda\project\packages',
                                         r'backend\aws_lambda\project\code\const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_METHODS' : general_info['T_METHODS'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_DATA_ORI': general_info['T_DATA_ORI'],
                                            'T_DATA_PREPROCESS': general_info['T_DATA_PREPROCESS'],
                                            'T_PROJECT_SUMMARY': general_info['T_PROJECT_SUMMARY'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                        },
                                        'generate_images.lambda_handler',
                                        'staging: generate images with preprocessing or augmentation methods')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'generate', 'images')

    # get current progress
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-generate-task-progress',
                                         [r'backend\aws_lambda\project\code\generate_task_progress.py', r'backend\aws_lambda\project\code\utils.py', 
                                         r'backend\aws_lambda\project\code\const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                            'T_PROJECT' : general_info['T_PROJECT']
                                        },
                                        'generate_task_progress.lambda_handler',
                                        'staging: get current progress of task_id')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'generate', 'task_progress')

    ### ========================###
    ## For balancer controller ####
    ### ========================###
    # lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-balancer-register_ec2',
    #                                      [r'backend\aws_lambda\project\code\balancer_register_ip.py', r'backend\aws_lambda\project\code\utils.py'],
    #                                     {
    #                                         'USER_POOL_ID' : general_info['USER_POOL_ID'],
    #                                         'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
    #                                         'T_TASKS' : general_info['T_TASKS'],
    #                                         'T_PROJECT' : general_info['T_PROJECT'],
    #                                         'T_INSTANCES': general_info['T_INSTANCES']
    #                                     },
    #                                     'balancer_register_ip.lambda_handler',
    #                                     'staging: register ec2 for new user')
    # add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'balancer', 'register_ec2')

    # process action start and stop 
    # lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-balancer-receiver',
    #                                      [r'backend\aws_lambda\project\code\balancer_receiver.py', r'backend\aws_lambda\project\code\utils.py'],
    #                                     {
    #                                         'USER_POOL_ID' : general_info['USER_POOL_ID'],
    #                                         'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
    #                                         'T_TASKS' : general_info['T_TASKS'],
    #                                         'T_PROJECT' : general_info['T_PROJECT'],
    #                                         'T_INSTANCES': general_info['T_INSTANCES']
    #                                     },
    #                                     'balancer_receiver.lambda_handler',
    #                                     'staging: receive request start stop from user')
    # add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'balancer', 'receiver')

    # async start ec2
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-balancer-asy-start',
                                         [r'backend\aws_lambda\project\code\balancer_asy_start.py', r'backend\aws_lambda\project\code\utils.py', 
                                         r'backend\aws_lambda\project\code\balancer_utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_INSTANCES': general_info['T_INSTANCES'],
                                            'IN_INSTANCES': 'index_ec2'
                                        },
                                        'balancer_asy_start.lambda_handler',
                                        'staging: start ec2')

    # async stop ec2
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-balancer-asy-stop',
                                         [r'backend\aws_lambda\project\code\balancer_asy_stop.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\balancer_utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_INSTANCES': general_info['T_INSTANCES'],
                                            'IN_INSTANCES': 'index_ec2',
                                            'T_EC2_TASK': general_info['T_EC2_TASK']
                                        },
                                        'balancer_asy_stop.lambda_handler',
                                        'staging: stop ec2')

    # async get ip ec2 of user_id
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-balancer-asy-get-ip',
                                         [r'backend\aws_lambda\project\code\balancer_asy_get_ip.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\balancer_utils.py',
                                         r'backend\aws_lambda\project\code\const.py'],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_INSTANCES': general_info['T_INSTANCES'],
                                            'IN_INSTANCES': 'index_ec2',
                                            'T_EC2_TASK': general_info['T_EC2_TASK']
                                        },
                                        'balancer_asy_get_ip.lambda_handler',
                                        'staging: get ip of user')

    # async get ip ec2 of user_id
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-balancer-asy-register',
                                         [r'backend\aws_lambda\project\code\balancer_asy_register_ec2.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\balancer_utils.py',
                                         r'backend\aws_lambda\project\code\const.py'
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_INSTANCES': general_info['T_INSTANCES'],
                                            'IN_INSTANCES': 'index_ec2',
                                            'T_EC2_TASK': general_info['T_EC2_TASK'],
                                        },
                                        'balancer_asy_register_ec2.lambda_handler',
                                        'staging: register ec2 for identity_id',
                                        timeout=500)

    # async update task finish for ec2
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-balancer-asy-finish-task',
                                         [r'backend\aws_lambda\project\code\balancer_asy_finish_task.py', r'backend\aws_lambda\project\code\utils.py',
                                         r'backend\aws_lambda\project\code\balancer_utils.py',
                                         r'backend\aws_lambda\project\code\const.py'
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'T_TASKS' : general_info['T_TASKS'],
                                            'T_PROJECT' : general_info['T_PROJECT'],
                                            'T_INSTANCES': general_info['T_INSTANCES'],
                                            'IN_INSTANCES': 'index_ec2',
                                            'T_EC2_TASK': general_info['T_EC2_TASK'],
                                        },
                                        'balancer_asy_finish_task.lambda_handler',
                                        'staging: process ec2 when finish a task')    

    return ls_lambda_val




    
