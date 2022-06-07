import json
import boto3
import hashlib
import hmac
import base64
import os
from boto3.dynamodb.conditions import Key, Attr
from utils import (
    convert_response,
    aws_get_identity_id,
    get_table_dydb_object,
    dydb_update_delete_project,
)


def lambda_handler(event, context):
    try:
        print(event["body"])
        body = json.loads(event["body"])

        # check authentication
        id_token = body["id_token"]
        identity_id = aws_get_identity_id(id_token)

        # get request data
        project_id = body["project_id"]
        project_name = body["project_name"]

        db_resource = boto3.resource("dynamodb")

        #### check task that belongs to the project id
        table = db_resource.Table(os.environ["T_TASKS"])
        response = table.query(
            KeyConditionExpression=Key("identity_id").eq(identity_id),
            FilterExpression=Attr("project_id").eq(project_id)
            & Attr("status").eq("RUNNING"),
        )
        if len(response["Items"]) > 0:
            raise Exception(
                f'There are {len(response["Items"])} tasks are running. Please stop all tasks before deleting the project!'
            )

        #### delete in project summary
        table = db_resource.Table(os.environ["T_PROJECT_SUMMARY"])
        for type_method in ["ORIGINAL", "PREPROCESS", "AUGMENT"]:
            table.delete_item(Key={"project_id": project_id, "type": type_method})

        #### delete project info
        table_project = db_resource.Table(os.environ["T_PROJECT"])
        table_project_delete = db_resource.Table(os.environ["T_PROJECT_DEL"])
        dydb_update_delete_project(
            table_project, table_project_delete, identity_id, project_name
        )

        print("after update delete")

        # delete in data
        for type_method in ["ORIGINAL", "PREPROCESS", "AUGMENT"]:
            table = get_table_dydb_object(db_resource, type_method)

            query = None
            with table.batch_writer() as batch:
                while query is None or "LastEvaluatedKey" in query:
                    if query is not None and "LastEvaluatedKey" in query:
                        query = table.query(
                            KeyConditionExpression=Key("project_id").eq(project_id),
                            ExclusiveStartKey=query["LastEvaluatedKey"],
                        )
                    else:
                        query = table.query(
                            KeyConditionExpression=Key("project_id").eq(project_id)
                        )

                    for item in query["Items"]:
                        batch.delete_item(
                            Key={"project_id": project_id, "filename": item["filename"]}
                        )

    except Exception as e:
        print("Error: ", repr(e))
        return convert_response(
            {"error": True, "success": False, "message": repr(e), "data": None}
        )

    return convert_response(
        {"data": {}, "error": False, "success": True, "message": None}
    )
