from datetime import datetime
import uuid

def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()

def create_unique_id():
    return str(uuid.uuid4())

def create_task_id_w_created_time():
    return f"{convert_current_date_to_iso8601()}-{create_unique_id()}"