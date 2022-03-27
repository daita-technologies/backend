from datetime import datetime
import uuid

def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()

def create_unique_id():
    return str(uuid.uuid4())