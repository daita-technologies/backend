from pathlib import Path
from aws_lambda.utils.utils import add_lambda_info_to_list

PROJECT_DIR = Path(__file__).parent
CODE_DIR = PROJECT_DIR.joinpath("code")

def deploy_lambda_auth(general_info, lambda_service):
    ls_lambda_val = []   
    
    #login
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'login',
                                          [ CODE_DIR.joinpath("login.py"),
                                            CODE_DIR.joinpath("utils.py"),
                                             PROJECT_DIR.joinpath("common"),
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID']
                                        },
                                        'login.lambda_handler',
                                        'staging: login')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'auth', 'user_login')

    # sign up
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'user_signup',
                                          [ CODE_DIR.joinpath("register.py"),
                                             PROJECT_DIR.joinpath("common"),
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID']
                                        },
                                        'register.lambda_handler',
                                        'staging: register')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'auth', 'user_signup')
    
    # login-social
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'login_social',
                                          [ CODE_DIR.joinpath("login_social.py"),
                                          CODE_DIR.joinpath("utils.py"),
                                        PROJECT_DIR.joinpath("packages"),
                                            PROJECT_DIR.joinpath("common"),
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID']
                                        },
                                        'login_social.lambda_handler',
                                        'staging: login_social')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'auth', 'login_social')    
    
    # template email
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'template_mail',
                                          [ CODE_DIR.joinpath("template_mail.py"),
                                            PROJECT_DIR.joinpath("common"),
                                            PROJECT_DIR.joinpath("packages")
                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID']
                                        },
                                        'template_mail.lambda_handler',
                                        'staging: template_mail')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'auth', 'template-invite-mail')
    
    # backend/lambda/login/module/auth/forgot_password.go
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-forgot-password',
                                        [
                                            CODE_DIR.joinpath("forgot_password.py"),
                                            PROJECT_DIR.joinpath("common"),
                                        ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID']
                                        },
                                        'forgot_password.lambda_handler',
                                        'staging: forgot password')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'auth', 'forgot-password')
    
    # backend/lambda/login/module/auth/confirm_code_forgot_password.go
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-confirm-code-forgot-password',
                                        [
                                            CODE_DIR.joinpath("confirm_code_forgot_password.py"),
                                            PROJECT_DIR.joinpath("common")
                                        ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID']
                                        },
                                        'confirm_code_forgot_password.lambda_handler',
                                        'staging: confirm code after request forgot password')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'auth', 'confirm-code-forgot-password')

    # backend/lambda/login/module/auth/login_refresh_token.go
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'staging-refresh-token',
                                        [
                                            CODE_DIR.joinpath("login_refresh_token.py"),
                                            CODE_DIR.joinpath("utils.py"),
                                            PROJECT_DIR.joinpath("common"),
                                        ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID']
                                        },
                                        'login_refresh_token.lambda_handler',
                                        'staging: Get refresh Token')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 'auth', 'refresh-token')

    return ls_lambda_val