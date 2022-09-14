import os

class LambdaEnv():
    def __init__(self) -> None:
        self.TABLE_ANNO_PROJECT = os.environ.get("TABLE_ANNO_PROJECT", "")
        self.TABLE_ANNO_DATA_ORI = os.environ.get("TABLE_ANNO_DATA_ORI", "")
        self.TABLE_ANNO_PROJECT_SUMMARY = os.environ.get("TABLE_ANNO_PROJECT_SUMMARY", "")

        self.S3_ANNO_BUCKET_NAME = os.environ.get("S3_ANNO_BUCKET_NAME", "")
        self.S3_DAITA_BUCKET_NAME = os.environ.get("S3_DAITA_BUCKET_NAME", "")

        self.TABLE_DAITA_DATA_ORIGINAL = os.environ.get("TABLE_DAITA_DATA_ORIGINAL", "")
        self.TABLE_DAITA_PROJECT = os.environ.get("TABLE_DAITA_PROJECT", "")

        self.SM_CLONE_PROJECT_ARN = os.environ.get("SM_CLONE_PROJECT_ARN", "") 

