from aws_lambda.lambda_service import AWSLambdaService
from aws_lambda.project.de_lambda_project_funcs import deploy_lambda_project
from aws_lambda.project.de_lambda_generate_funcs import deploy_lambda_generate
from aws_lambda.project.de_lambda_balancer_funcs import deploy_lambda_balancer
from aws_lambda.project.de_lambda_auth_funcs import deploy_lambda_auth

from aws_lambda.project.de_lambda_webhook import deploy_lambda_webhook


def deploy_lambda(general_info):
    lambda_service = AWSLambdaService()
    ls_lambda_val = []

    # ls_lambda_val += deploy_lambda_project(general_info, lambda_service)
    # ls_lambda_val += deploy_lambda_generate(general_info, lambda_service)
    # ls_lambda_val += deploy_lambda_balancer(general_info, lambda_service)
    ls_lambda_val += deploy_lambda_auth(general_info, lambda_service)
    # ls_lambda_val += deploy_lambda_webhook(general_info, lambda_service)    

    return ls_lambda_val




    