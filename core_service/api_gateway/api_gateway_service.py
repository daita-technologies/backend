from botocore.exceptions import ClientError
import logging
import json
import time

logger = logging.getLogger(__name__)


class ApiGatewayToService:
    """
    Encapsulates Amazon API Gateway functions that are used to create a REST API that
    integrates with another AWS service.
    """

    def __init__(self, apig_client):
        """
        :param apig_client: A Boto3 API Gateway client.
        """
        self.apig_client = apig_client
        self.api_id = None
        self.root_id = None
        self.stage = None
        self.resources = None

    def create_rest_api(self, api_name):
        """
        Creates a REST API on API Gateway. The default API has only a root resource
        and no HTTP methods.

        :param api_name: The name of the API. This descriptive name is not used in
                         the API path.
        :return: The ID of the newly created API.
        """
        try:
            # get api id if this api_name exist. AWS will not make the api_name is unique, so we have to check it
            rest_api_id = self.get_rest_api_id(api_name)
            self.api_id = rest_api_id
        except Exception as e:
            try:
                result = self.apig_client.create_rest_api(name=api_name)
                self.api_id = result["id"]
                logger.info("Created REST API %s with ID %s.", api_name, self.api_id)
            except ClientError:
                logger.exception("Couldn't create REST API %s.", api_name)
                raise

        try:
            result = self.apig_client.get_resources(restApiId=self.api_id, limit=200)
            self.resources = result
            self.root_id = next(
                item for item in result["items"] if item["path"] == "/"
            )["id"]
        except ClientError:
            logger.exception("Couldn't get resources for API %s.", self.api_id)
            raise
        except StopIteration as err:
            logger.exception("No root resource found in API %s.", self.api_id)
            raise ValueError from err

        return self.api_id

    def add_rest_resource(self, parent_id, resource_path):
        """
        Adds a resource to a REST API.

        :param parent_id: The ID of the parent resource.
        :param resource_path: The path of the new resource, relative to the parent.
        :return: The ID of the new resource.
        """

        # check if resource exist
        for item in list(self.resources["items"]):
            if (
                item.get("pathPart", "") == resource_path
                and item["parentId"] == parent_id
            ):
                return item["id"]

        # if not, create new one
        try:
            result = self.apig_client.create_resource(
                restApiId=self.api_id, parentId=parent_id, pathPart=resource_path
            )
            resource_id = result["id"]
            logger.info("Created resource %s.", resource_path)
        except ClientError:
            logger.exception(
                "Couldn't create resource %s/%s.", parent_id, resource_path
            )
            raise
        else:
            return resource_id

    def add_integration_method(
        self,
        resource_id,
        rest_method,
        service_uri,
        lambda_version,
        service_method,
        role_arn,
        mapping_template,
    ):
        """
        Adds an integration method to a REST API. An integration method is a REST
        resource, such as '/users', and an HTTP verb, such as GET. The integration
        method is backed by an AWS service, such as Amazon DynamoDB.

        :param resource_id: The ID of the REST resource.
        :param rest_method: The HTTP verb used with the REST resource.
        :param service_uri: The service endpoint that is integrated with
                                        this method, such as 'dynamodb'.
        :param lambda_version: The version of client that create lambda
        :param service_method: The HTTP method of the service request, such as POST.
        :param role_arn: The Amazon Resource Name (ARN) of a role that grants API
                         Gateway permission to use the specified action with the
                         service.
        :param mapping_template: A mapping template that is used to translate REST
                                 elements, such as query parameters, to the request
                                 body format required by the service.
        """

        is_exist = False
        try:
            self.apig_client.put_method(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod=rest_method,
                authorizationType="NONE",
            )
            self.apig_client.put_method_response(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod=rest_method,
                statusCode="200",
                responseModels={"application/json": "Empty"},
            )
            logger.info("Created %s method for resource %s.", rest_method, resource_id)
        except ClientError as err:
            if (
                err.response["Error"]["Code"] == "ConflictException"
                and err.response["Error"]["Message"]
                == "Method already exists for this resource"
            ):
                # method already exist, so we will update, not create new
                is_exist = True
                print(f"Medthod {resource_id} already exists")

        if is_exist:
            # delete old integration
            try:
                response = self.apig_client.delete_integration(
                    restApiId=self.api_id,
                    resourceId=resource_id,
                    httpMethod=rest_method,
                )
            except ClientError as err:
                raise err

        response = None
        times_try = 0
        while times_try < 5 and response is None:
            try:
                uri = f"arn:aws:apigateway:{self.apig_client.meta.region_name}:lambda:path/{lambda_version}/functions/{service_uri}/invocations"
                response = self.apig_client.put_integration(
                    restApiId=self.api_id,
                    resourceId=resource_id,
                    httpMethod=rest_method,
                    type="AWS_PROXY",
                    integrationHttpMethod=service_method,
                    credentials=role_arn,
                    # requestTemplates={'application/json': json.dumps(mapping_template)},
                    uri=uri,
                )
                self.apig_client.put_integration_response(
                    restApiId=self.api_id,
                    resourceId=resource_id,
                    httpMethod=rest_method,
                    statusCode="200",
                    responseTemplates={"application/json": ""},
                )
                logger.info(
                    "Created integration for resource %s to service URI %s.",
                    resource_id,
                    uri,
                )
            except ClientError:
                print(
                    "Couldn't create integration for resource %s to service URI %s.",
                    resource_id,
                    uri,
                )
                times_try += 1
                time.sleep(2)

        if response is None:
            raise Exception("Could not integrate lambda function to API")

    def add_integration_cors(self, resource_id):
        try:
            self.apig_client.put_method(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod="OPTIONS",
                authorizationType="NONE",
            )

            self.apig_client.put_integration(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod="OPTIONS",
                type="MOCK",
                requestTemplates={"application/json": '{"statusCode": 200}'},
            )

            # Set the put method response of the OPTIONS method
            self.apig_client.put_method_response(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod="OPTIONS",
                statusCode="200",
                responseParameters={
                    "method.response.header.Access-Control-Allow-Headers": False,
                    "method.response.header.Access-Control-Allow-Origin": False,
                    "method.response.header.Access-Control-Allow-Methods": False,
                },
                responseModels={"application/json": "Empty"},
            )

            # Set the put integration response of the OPTIONS method
            self.apig_client.put_integration_response(
                restApiId=self.api_id,
                resourceId=resource_id,
                httpMethod="OPTIONS",
                statusCode="200",
                responseParameters={
                    "method.response.header.Access-Control-Allow-Headers": "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                    "method.response.header.Access-Control-Allow-Methods": "'POST,OPTIONS'",
                    "method.response.header.Access-Control-Allow-Origin": "'*'",
                },
                responseTemplates={"application/json": ""},
            )
        except Exception as e:
            a = 1

    def deploy_api(self, stage_name):
        """
        Deploys a REST API. After a REST API is deployed, it can be called from any
        REST client, such as the Python Requests package or Postman.

        :param stage_name: The stage of the API to deploy, such as 'test'.
        :return: The base URL of the deployed REST API.
        """
        try:
            self.apig_client.create_deployment(
                restApiId=self.api_id, stageName=stage_name
            )
            self.stage = stage_name
            logger.info("Deployed stage %s.", stage_name)
        except ClientError:
            logger.exception("Couldn't deploy stage %s.", stage_name)
            raise
        else:
            return self.api_url()

    def api_url(self, resource=None):
        """
        Builds the REST API URL from its parts.

        :param resource: The resource path to append to the base URL.
        :return: The REST URL to the specified resource.
        """
        url = (
            f"https://{self.api_id}.execute-api.{self.apig_client.meta.region_name}"
            f".amazonaws.com/{self.stage}"
        )
        if resource is not None:
            url = f"{url}/{resource}"
        return url

    def get_rest_api_id(self, api_name):
        """
        Gets the ID of a REST API from its name by searching the list of REST APIs
        for the current account. Because names need not be unique, this returns only
        the first API with the specified name.

        :param api_name: The name of the API to look up.
        :return: The ID of the specified API.
        """
        try:
            rest_api = None
            paginator = self.apig_client.get_paginator("get_rest_apis")
            for page in paginator.paginate():
                rest_api = next(
                    (item for item in page["items"] if item["name"] == api_name), None
                )
                if rest_api is not None:
                    break
            self.api_id = rest_api["id"]
            logger.info("Found ID %s for API %s.", rest_api["id"], api_name)
        except ClientError:
            logger.exception("Couldn't find ID for API %s.", api_name)
            raise
        else:
            return rest_api["id"]

    def delete_rest_api(self):
        """
        Deletes a REST API, including all of its resources and configuration.
        """
        try:
            self.apig_client.delete_rest_api(restApiId=self.api_id)
            logger.info("Deleted REST API %s.", self.api_id)
            self.api_id = None
        except ClientError:
            logger.exception("Couldn't delete REST API %s.", self.api_id)
            raise
