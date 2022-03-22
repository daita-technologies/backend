from datetime import datetime

def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()