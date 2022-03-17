from aws_lambda.utils.utils import add_lambda_info_to_list
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
ROOT = str(PROJECT_DIR.joinpath("code"))+'/'
PACKAGES = PROJECT_DIR.joinpath("packages")

def deploy_lambda_balancer(general_info, lambda_service):
    ls_lambda_val = [] 
        
    # async start ec2
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-balancer-asy-start-test',
                                         [ROOT + 'balancer_asy_start.py', ROOT + 'utils.py', 
                                         ROOT + 'balancer_utils.py',
                                         ROOT + 'const.py'],
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
                                         [ROOT + 'balancer_asy_stop.py', ROOT + 'utils.py',
                                         ROOT + 'balancer_utils.py',
                                         ROOT + 'const.py'],
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
                                         [ROOT + 'balancer_asy_get_ip.py', ROOT + 'utils.py',
                                         ROOT + 'balancer_utils.py',
                                         ROOT + 'const.py'],
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
                                         [ROOT + 'balancer_asy_register_ec2.py', ROOT + 'utils.py',
                                         ROOT + 'balancer_utils.py',
                                         ROOT + 'const.py'
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
                                         [ROOT + 'balancer_asy_finish_task.py', ROOT + 'utils.py',
                                         ROOT + 'balancer_utils.py',
                                         ROOT + 'const.py'
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




    