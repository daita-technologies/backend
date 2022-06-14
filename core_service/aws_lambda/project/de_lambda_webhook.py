from pathlib import Path
from aws_lambda.utils.utils import add_lambda_info_to_list

PROJECT_DIR = Path(__file__).parent
CODE_DIR = PROJECT_DIR.joinpath("code")

def deploy_lambda_webhook(general_info, lambda_service):
    ls_lambda_val = []   
    
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'slack_webhook_feedback',
                                          [ CODE_DIR.joinpath("slack_webhook_feedback.py"),
                                             PROJECT_DIR.joinpath("common"),
                                              PROJECT_DIR.joinpath("packages")
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID']
                                        },
                                        'slack_webhook_feedback.lambda_handler',
                                        'staging: slack_webhook_feedback')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'webhook', 'client-feedback')

    return ls_lambda_val