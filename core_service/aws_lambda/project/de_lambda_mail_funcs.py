from pathlib import Path
from aws_lambda.utils.utils import add_lambda_info_to_list

PROJECT_DIR = Path(__file__).parent
CODE_DIR = PROJECT_DIR.joinpath("code")

def deploy_lambda_send_mail(general_info, lambda_service):
    ls_lambda_val = []   
    
    #reference-email
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'reference-email',
                                          [ CODE_DIR.joinpath("invite_friend.py"),
                                            CODE_DIR.joinpath("utils.py"),
                                            PROJECT_DIR.joinpath("common")
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'MODE': general_info['MODE']
                                        },
                                        'invite_friend.lambda_handler',
                                        'staging: reference-email')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'send-mail', 'reference-email')
    #reference-email
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-sendmail-cognito-service',
                                          [ CODE_DIR.joinpath("cognito_send_mail.py")
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'MODE': general_info['MODE']
                                        },
                                        'cognito_send_mail.lambda_handler',
                                        'staging: cognito_send_mail')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'send-mail', 'staging-sendmail-cognito-service')
    return ls_lambda_val