import boto3
import os

from utils import convert_response
from balancer_utils import get_ec2_id_link_user, get_ec2_available, db_write_assign_id


def lambda_handler(event, context):

    # try to parse request body and check body fields
    try:
        print(event)
        identity_id = event["identity_id"]

    except Exception as e:
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    try:
        db_resource = boto3.resource("dynamodb")
        table = db_resource.Table(os.environ["T_INSTANCES"])

        # check already had the ec2 that linked with indentity_id
        ec2_id = get_ec2_id_link_user(table, identity_id)

        if ec2_id is None:
            # get available ec2 that will assign to this user, if not found free ec2, assign to the default ec2
            ec2_avai = get_ec2_available(table)
            if ec2_avai is None:
                raise Exception(f"No ec2 available now, please check default ec2 on DB")

            # write info to DB
            db_write_assign_id(table, identity_id, ec2_avai)
        else:
            raise Exception(
                f"This user id {identity_id} already assiged to ec2_id {ec2_id}"
            )

    except Exception as e:
        print("Error: ", repr(e))
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    return convert_response(
        {"data": None, "error": False, "success": True, "message": None}
    )
