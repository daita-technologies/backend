from .dynamodb_service import DynamoDBService


def deploy_dynamoDB(general_info):
    dbservice = DynamoDBService()

    dbservice.create_bd(
        general_info["T_PROJECT"],
        [("identity_id", "HASH", "S"), ("project_name", "RANGE", "S")],
    )  # range means short key, hash means partition key
    dbservice.create_bd(
        general_info["T_PROJECT_DEL"],
        [("identity_id", "HASH", "S"), ("project_name", "RANGE", "S")],
    )  # range means short key, hash means partition key
    dbservice.create_bd(
        general_info["T_DATA_ORI"],
        [("project_id", "HASH", "S"), ("filename", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_DATA_PREPROCESS"],
        [("project_id", "HASH", "S"), ("filename", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_DATA_AUGMENT"],
        [("project_id", "HASH", "S"), ("filename", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_PROJECT_SUMMARY"],
        [("project_id", "HASH", "S"), ("type", "RANGE", "S")],
    )  # type is one of 'ORI', 'PRE', 'AUG'
    dbservice.create_bd(
        general_info["T_TASKS"],
        [("identity_id", "HASH", "S"), ("task_id", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_METHODS"],
        [("method_id", "HASH", "S"), ("method_name", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_QUOTAS"],
        [("identity_id", "HASH", "S"), ("type", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_INSTANCES"],
        [("ec2_id", "HASH", "S"), ("assi_id", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_EC2_TASK"],
        [("ec2_id", "HASH", "S"), ("task_id", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_TASK_DOWNLOAD"],
        [("identity_id", "HASH", "S"), ("task_id", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_TRIGGER_SEND_CODE"],
        [("user", "HASH", "S"), ("code", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_EVENT_USER"],
        [("event_ID", "HASH", "S"), ("type", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_USER"],
        [("ID", "HASH", "S"), ("username", "RANGE", "S")],
    )
    dbservice.create_bd(
        general_info["T_FEEDBACK"],
        [
            ("ID", "HASH", "S"),
        ],
    )
