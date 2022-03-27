import os
import json
import uuid

import boto3


stepfunctions = boto3.client('stepfunctions')
EFS_MOUNT_POINT = "/mnt/efs"


def lambda_handler(event, context):
    print(event)
    body = json.loads(event["body"])

    # file path in S3
    file_url = body["file_url"]
    id_token = body["id_token"]
    project_id = body['project_id']
    project_name = body['project_name']
    type_method = body.get('type_method', 'ORIGINAL')
    # command = body["command"]

    # building decompress command
    working_dir = os.path.join(EFS_MOUNT_POINT, "app", "decompress", str(uuid.uuid4()))
    filename = os.path.basename(file_url)
    file_stemp = os.path.splitext(filename)[0]
    destination_dir = os.path.join(working_dir, file_stemp)
    container_commands = [
        f"mkdir -p {working_dir}",
        f"cd {working_dir}",
        f"/usr/local/bin/aws s3 cp {file_url} {filename}",
        f"unzip {filename} -d {destination_dir}",
        f"rm {filename}"
    ]
    container_command = " && ".join(container_commands)
    command = [
        "/bin/bash",
        "-c",
        container_command
    ]

    task_input = {
        "file_url": file_url,
        "id_token": id_token,
        "project_id": project_id,
        "project_name": project_name,
        "type_method": type_method,
        "filename": filename,
        "destination_dir": destination_dir,
        "command": command
    }
    response = stepfunctions.start_execution(
        stateMachineArn=os.getenv("DecompressFileStateMachineArn"),
        input=json.dumps(task_input)
    )

    # create task record in db
    # return task id for frontend

    print("succeed")
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "succeed",
            "file_url": file_url
        }),
    }
