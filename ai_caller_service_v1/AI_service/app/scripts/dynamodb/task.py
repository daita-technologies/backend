import boto3
from datetime import datetime


def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()


# PENDING|PREPARING_HARDWARE|PREPARING_DATA|RUNNING|UPLOADING|FINISH or ERROR
class TasksModel(object):
    def __init__(self):
        self.db_client = boto3.resource("dynamodb", region_name="us-east-2")
        self.num_gens = None

    def create_item(
        self, identity_id, task_id, project_id, num_gens, process_type, IP, EC2_ID
    ):
        self.db_client.Table("tasks").put_item(
            Item={
                "identity_id": identity_id,
                "task_id": task_id,
                "project_id": project_id,
                "status": "PENDING",
                "number_gen_images": num_gens,
                "process_type": process_type,
                "IP": IP,
                "EC2_ID": EC2_ID,
                "created_time": convert_current_date_to_iso8601(),
                "updated_time": convert_current_date_to_iso8601(),
                "number_finished": 0,
            }
        )

    def update_finish(self, task_id, identity_id, num_gens, IP, EC2_ID):
        self.db_client.Table("tasks").update_item(
            Key={"task_id": task_id, "identity_id": identity_id},
            UpdateExpression="SET #s=:s, #num_finished=:num_finished, #updated_time=:updated_time, #IP=:IP, #EC2_ID=:EC2_ID",
            ExpressionAttributeValues={
                ":s": "FINISH",
                ":num_finished": num_gens,
                ":IP": IP,
                ":EC2_ID": EC2_ID,
                ":updated_time": convert_current_date_to_iso8601(),
            },
            ExpressionAttributeNames={
                "#s": "status",
                "#IP": "IP",
                "#EC2_ID": "EC2_ID",
                "#updated_time": "updated_time",
                "#num_finished": "number_finished",
            },
        )

    def update_process(self, task_id, identity_id, num_finish, status):
        self.db_client.Table("tasks").update_item(
            Key={"task_id": task_id, "identity_id": identity_id},
            UpdateExpression="SET #s=:s, #num_finished=:num_finished, #updated_time=:updated_time",
            ExpressionAttributeValues={
                ":s": status,
                ":num_finished": num_finish,
                ":updated_time": convert_current_date_to_iso8601(),
            },
            ExpressionAttributeNames={
                "#s": "status",
                "#updated_time": "updated_time",
                "#num_finished": "number_finished",
            },
        )

    def update_process_uploading(self, task_id, identity_id):
        self.db_client.Table("tasks").update_item(
            Key={"task_id": task_id, "identity_id": identity_id},
            UpdateExpression="SET #s=:s, #updated_time=:updated_time",
            ExpressionAttributeValues={
                ":s": "UPLOADING",
                ":updated_time": convert_current_date_to_iso8601(),
            },
            ExpressionAttributeNames={"#s": "status", "#updated_time": "updated_time"},
        )

    def update_process_error(self, task_id, identity_id, IP, EC2_ID):
        self.db_client.Table("tasks").update_item(
            Key={"task_id": task_id, "identity_id": identity_id},
            UpdateExpression="SET #s=:s, #updated_time=:updated_time,#IP=:IP,#EC2_ID=:EC2_ID",
            ExpressionAttributeValues={
                ":s": "ERROR",
                ":IP": IP,
                ":EC2_ID": EC2_ID,
                ":updated_time": convert_current_date_to_iso8601(),
            },
            ExpressionAttributeNames={
                "#s": "status",
                "#IP": "IP",
                "#EC2_ID": "EC2_ID",
                "#updated_time": "updated_time",
            },
        )
