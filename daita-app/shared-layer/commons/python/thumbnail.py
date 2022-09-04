
class Thumbnail(object):
    def __init__(self,info) -> None:
        self.project_ID = info['project_id']
        self.filename = info['filename']
        self.thumbnail = None
        self.s3_url = info['s3_urls']
        self.table_name  = info['table']