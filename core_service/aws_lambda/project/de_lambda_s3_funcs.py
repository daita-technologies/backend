from pathlib import Path
from aws_lambda.utils.utils import add_lambda_info_to_list

PROJECT_DIR = Path(__file__).parent
CODE_DIR = PROJECT_DIR.joinpath("code")

def deploy_lambda_s3(general_info, lambda_service):
    ls_lambda_val = []
    lambda_uri, lambda_version = lambda_service.deploy_lambda_function(f'presigned-url-3',
                                          [ CODE_DIR.joinpath("presigned_url_s3.py"),
                                             PROJECT_DIR.joinpath("common")                                         ],
                                        {
                                            'USER_POOL_ID' : general_info['USER_POOL_ID'],
                                            'IDENTITY_POOL_ID': general_info['IDENTITY_POOL_ID'],
                                            'BUCKET_NAME': general_info['BUCKET_NAME']
                                        },
                                        'presigned_url_s3.lambda_handler',
                                        'staging: presigned_url_s3.py')
    add_lambda_info_to_list(ls_lambda_val, lambda_uri, lambda_version, 's3', 'presigned-url')
    return ls_lambda_val