import json
import boto3
import hashlib
import hmac
import base64
import os
import uuid
from boto3.dynamodb.conditions import Key, Attr

from utils import (
    convert_response,
    convert_current_date_to_iso8601,
    aws_get_identity_id,
    get_num_prj,
)
import const


def lambda_handler(event, context):
    try:
        print(event["body"])
        body = json.loads(event["body"])
        id_token = body["id_token"]
        access_token = body["access_token"]
        project_name = body["project_name"]
        project_info = body.get("project_info", "")
    except Exception as e:
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    try:
        identity_id = aws_get_identity_id(id_token)
    except Exception as e:
        print("Error: ", repr(e))
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    db_resource = boto3.resource("dynamodb")

    # check number of created project of user
    try:
        # check length of projectname and project info
        if len(project_name) > const.MAX_LENGTH_PROJECT_NAME_INFO:
            raise Exception(const.MES_LENGTH_OF_PROJECT_NAME)
        if len(project_info) > const.MAX_LENGTH_PROJECT_NAME_INFO:
            raise Exception(const.MES_LENGTH_OF_PROJECT_INFO)

        num_prj = get_num_prj(identity_id)
        if num_prj >= const.MAX_NUM_PRJ_PER_USER:
            raise Exception(const.MES_REACH_LIMIT_NUM_PRJ)

        # db_resource = boto3.resource("dynamodb")
        # table = db_resource.Table(os.environ['T_QUOTAS'])
        # response = table.get_item(
        #         Key = {
        #             "identity_id": identity_id,
        #             "type": "NUM_PRJ"
        #         }
        #     )
        # if response.get('Item'):
        #     current_num = response['Item'].get("num_current", 0)

        # else:
        #     current_num = 0

    except Exception as e:
        print("Error: ", repr(e))
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    # co_client = boto3.client('cognito-idp')
    # try:
    #     response = co_client.get_user(
    #         AccessToken=access_token
    #     )
    #     print(f'response access token: \n {response}')
    # except Exception as e:
    #     print('Error: ', repr(e))
    #     return convert_response({"error": True,
    #             "success": False,
    #             "message": repr(e),
    #             "data": None})
    # sub = [a['Value'] for a in response['UserAttributes'] if a['Name'] == 'sub'][0]

    _uuid = uuid.uuid4().hex
    project_id = f"{project_name}_{_uuid}"
    s3_prefix = f'{os.environ["BUCKET_NAME"]}/{identity_id}/{project_id}'
    db_client = boto3.client("dynamodb")
    try:
        is_sample = False
        gen_status = "FINISH"
        table_prj = db_resource.Table(os.environ["T_PROJECT"])
        table_prj.put_item(
            Item={
                "ID": _uuid,
                "project_id": project_id,
                "identity_id": identity_id,
                "project_name": project_name,
                "s3_prefix": s3_prefix,
                "project_info": project_info,
                # 'sub': sub,
                "created_date": convert_current_date_to_iso8601(),
                "is_sample": is_sample,
                "gen_status": gen_status,
            },
            ConditionExpression=Attr("project_name").not_exists()
            & Attr("identity_id").not_exists(),
        )

        # # update quotas
        # table.update_item(
        #             Key={
        #                 'identity_id': identity_id,
        #                 'type': "NUM_PRJ",
        #             },
        #             ExpressionAttributeNames= {
        #                 '#NC': "num_current"
        #             },
        #             ExpressionAttributeValues = {
        #                 ':nc':  current_num + 1,
        #             },
        #             UpdateExpression = 'SET #NC = :nc'
        #         )

    except db_resource.meta.client.exceptions.ConditionalCheckFailedException as e:
        print("Error condition: ", e)
        err_mess = const.MES_DUPLICATE_PROJECT_NAME.format(project_name)
        return convert_response(
            {"error": True, "success": False, "message": err_mess, "data": None}
        )
    except Exception as e:
        print("Error: ", e)
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    return convert_response(
        {
            "data": {
                "project_id": project_id,
                "s3_prefix": s3_prefix,
                "is_sample": is_sample,
                "gen_status": gen_status,
                "project_name": project_name,
            },
            "error": False,
            "success": True,
            "message": None,
        }
    )
