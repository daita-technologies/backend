import boto3

from backend.api_gateway.api_gateway_service import ApiGatewayToService

def deploy_api_project(ls_lambda_info, general_info):
    REST_API_NAME = 'staging-daita-project'
    RESOURCE_PROJECT = 'projects'
    RESOURCE_GENERATE = 'generate'
    RESOURCE_BALANCER = 'balancer'
    STAGES = general_info['MODE']
    API_GW_ROLE = 'arn:aws:iam::737589818430:role/daita_apigw_lambda_cloud_watch'
    gateway = ApiGatewayToService(boto3.client('apigateway'))
    gateway.create_rest_api(REST_API_NAME)
    project_id = gateway.add_rest_resource(gateway.root_id, RESOURCE_PROJECT)
    generate_id = gateway.add_rest_resource(gateway.root_id, RESOURCE_GENERATE)
    balancer_id = gateway.add_rest_resource(gateway.root_id, RESOURCE_BALANCER)

    for lambda_uri, lambda_version, api_resource, api_name in ls_lambda_info:  
        if api_resource == 'project':
            resource_id_choose = project_id
        elif api_resource == 'generate':
            resource_id_choose = generate_id
        elif api_resource == 'balancer':
            resource_id_choose = balancer_id
        else:
            resource_id_choose = project_id
        
        function_resource_id = gateway.add_rest_resource(resource_id_choose, api_name)
        gateway.add_integration_method(
            function_resource_id, 'POST', lambda_uri, lambda_version,'POST', API_GW_ROLE, '')
        gateway.add_integration_cors(function_resource_id)

    gateway.deploy_api(STAGES)

    a=1
