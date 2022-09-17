from genericpath import exists, isfile
import os
from pathlib import Path
import boto3

CLUSTER_NAME = os.getenv("CLUSTER_NAME")
TASK_DEFINITION = os.getenv("TASK_DEFINITION")
SECURITY_GROUP_ID = os.getenv("SECURITY_GROUP_ID")
SUBNET_ID = os.getenv("SUBNET_ID")

client = boto3.client('ecs')


def lambda_handler(event, context):
    try:
        # trigger ECS job
        response = client.run_task(
            cluster=CLUSTER_NAME,
            taskDefinition=TASK_DEFINITION,
            count=1,
            networkConfiguration={
                'awsvpcConfiguration': {
                    'subnets': [
                        SUBNET_ID
                    ],
                    'securityGroups': [
                        SECURITY_GROUP_ID
                    ],
                }
            },
            overrides={

            }
        )

        print(response)

        return {
            'statusCode': 200,
            'body': "OK",
            'meta': f"{CLUSTER_NAME}, {TASK_DEFINITION}, {SUBNET_ID}, {SECURITY_GROUP_ID}"
        }
    except Exception as e:
        print(e)

        return {
            'statusCode': 500,
            'body': str(e),
            'meta': "   "
        }