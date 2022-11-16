import os

class LambdaEnv():
    def __init__(self) -> None:

        self.USER_POOL_ID = os.environ.get('COGNITO_USER_POOL', "")
        self.IDENTITY_POOL_ID = os.environ.get('IDENTITY_POOL', "")

        self.TABLE_ANNO_PROJECT = os.environ.get("TABLE_ANNO_PROJECT", "")
        self.TABLE_ANNO_DATA_ORI = os.environ.get("TABLE_ANNO_DATA_ORI", "")
        self.TABLE_ANNO_PROJECT_SUMMARY = os.environ.get("TABLE_ANNO_PROJECT_SUMMARY", "")
        self.TABLE_ANNO_LABEL_INFO = os.environ.get("TABLE_ANNO_LABEL_INFO", "")
        self.TABLE_ANNO_CATEGORY_INFO = os.environ.get("TABLE_ANNO_CATEGORY_INFO", "")
        self.TABLE_ANNO_CLASS_INFO = os.environ.get("TABLE_ANNO_CLASS_INFO", "")
        self.TABLE_ANNO_AI_DEFAULT_CLASS = os.environ.get("TABLE_ANNO_AI_DEFAULT_CLASS", "")
        self.TABLE_ANNO_DELETED_PRJ = os.environ.get("TABLE_ANNO_DELETED_PRJ", "")

        self.S3_ANNO_BUCKET_NAME = os.environ.get("S3_ANNO_BUCKET_NAME", "")
        self.S3_DAITA_BUCKET_NAME = os.environ.get("S3_DAITA_BUCKET_NAME", "")

        self.TABLE_DAITA_DATA_ORIGINAL = os.environ.get("TABLE_DAITA_DATA_ORIGINAL", "")
        self.TABLE_DAITA_PROJECT = os.environ.get("TABLE_DAITA_PROJECT", "")

        self.TABLE_CONFIG_PARA_LAMBDA = os.environ.get("TABLE_CONFIG_PARA_LAMBDA", "")

        self.TABLE_GENERATE_TASK = os.environ.get("TABLE_GENERATE_TASK", "")

        self.SM_CLONE_PROJECT_ARN = os.environ.get("SM_CLONE_PROJECT_ARN", "") 

        self.FUNC_DAITA_UPLOAD_UPDATE = os.environ.get("FUNC_DAITA_UPLOAD_UPDATE", "")

        self.IS_USE_ECS_AI_CALLER_FLOW = os.environ.get("IS_USE_ECS_AI_CALLER_FLOW", False)
        self.AI_CALLER_ECS_SM_ARN = os.environ.get("AI_CALLER_ECS_SM_ARN", "")

