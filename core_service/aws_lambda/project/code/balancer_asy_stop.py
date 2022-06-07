import boto3

from utils import convert_response, aws_get_identity_id, dydb_get_task_progress


def lambda_handler(event, context):

    # try to parse request body and check body fields
    try:
        print(event)
        ec2_id = event["ec2_id"]

    except Exception as e:
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    try:
        ec2_resource = boto3.resource("ec2", region_name="us-east-2")
        instance = ec2_resource.Instance(ec2_id)
        if instance is None:
            raise Exception(f"Instance id {ec2_id} does not exist")

        if instance.state["Name"] == "stopped":
            print("Instance id {ec2_id} stopped => no process")

        elif instance.state["Name"] == "running":
            print("Instance id {ec2_id} running => stop")
            instance.stop()

    except Exception as e:
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    return convert_response(
        {"data": None, "error": False, "success": True, "message": None}
    )
