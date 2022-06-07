import boto3
import botocore
from aws_lambda.utils.utils import create_zip_object


class AWSLambdaService:
    def __init__(self):
        """
        init for lambda service
        """
        self.client = boto3.client("lambda")
        self.version = self.client.meta.service_model.api_version

    def deploy_lambda_function(
        self,
        function_name,
        ls_files,
        env_vari,
        handler,
        description,
        timeout=400,
        memorysize=128,
    ):

        zip_file = create_zip_object(ls_files)
        try:
            response = self.client.create_function(
                Code={"ZipFile": zip_file},
                PackageType="Zip",
                Description=description,
                Environment={
                    "Variables": env_vari,
                },
                FunctionName=function_name,
                Handler=handler,
                # KMSKeyArn='',   # use as default of Lambda service key
                MemorySize=memorysize,
                Publish=True,
                Role="arn:aws:iam::366577564432:role/role_lambda",
                Runtime="python3.8",
                Tags={
                    "DEPARTMENT": "Assets",
                },
                Timeout=timeout,
                TracingConfig={
                    "Mode": "Active",
                },
            )
            self.client.get_waiter("function_active").wait(FunctionName=function_name)

            try:
                self.client.get_waiter("function_updated").wait(
                    FunctionName=function_name
                )

                # update code to make sure that function is available to assign in api
                response = self.client.update_function_code(
                    FunctionName=function_name, ZipFile=zip_file, Publish=True
                )
                self.client.get_waiter("function_updated").wait(
                    FunctionName=function_name
                )
            except Exception as e:
                raise e

            return response["FunctionArn"], self.version

        except botocore.exceptions.ClientError as err:
            if (
                err.response["Error"]["Code"] == "ResourceConflictException"
                and "Function already exist" in err.response["Error"]["Message"]
            ):
                try:
                    # update configuration for variables
                    response = self.client.update_function_configuration(
                        FunctionName=function_name,
                        Environment={
                            "Variables": env_vari,
                        },
                        MemorySize=memorysize,
                        Timeout=timeout,
                    )
                    self.client.get_waiter("function_updated").wait(
                        FunctionName=function_name
                    )

                    response = self.client.update_function_code(
                        FunctionName=function_name, ZipFile=zip_file, Publish=True
                    )
                    self.client.get_waiter("function_updated").wait(
                        FunctionName=function_name
                    )
                except Exception as exp:
                    raise exp

                return response["FunctionArn"], self.version
            else:
                raise err
        except Exception as e:
            raise e
