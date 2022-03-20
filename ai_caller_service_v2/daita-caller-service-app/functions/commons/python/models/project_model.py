import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *



class ProjectItem():
    FIELD_IDENTITY_ID   = "identity_id"
    FIELD_PROJECT_ID    = "project_id"
    FIELD_PROJECT_NAME  = "project_name"
    FIELD_GEN_STATUS    = "gen_status"
    FIELD_S3_PREFIX     = "s3_prefix"
    FIELD_IS_SAMPLE     = "is_sample"
    FIELD_PROJECT_INFO  = "project_info"
    FIELD_TIMES_AUGMENT = "times_generated"
    FIELD_TIMES_PREPRO  = "times_propr"

    def __init__(self, dict_info) -> None:        
        print("start init")
        for key, value in dict_info.items():
            self.__dict__[key]=value
        print("init success: ", self.__dict__)

    def get_value_w_default(self, name, default_value):
        if self.__dict__.get(name, None):
            return self.__dict__[name]
        else:
            self.__dict__[name] = default_value
            return default_value


class ProjectModel():
    def __init__(self) -> None:
        self.table = boto3.resource('dynamodb').Table(DB_PROJECT_TABLE_NAME)               
   
    def get_project_info(self, identity_id, project_name) -> ProjectItem:            
        response = self.table.get_item(
            Key={
                ProjectItem.FIELD_IDENTITY_ID: identity_id,
                ProjectItem.FIELD_PROJECT_NAME: project_name,
            },
            ProjectionExpression= f'{ProjectItem.FIELD_PROJECT_ID}, {ProjectItem.FIELD_S3_PREFIX}, {ProjectItem.FIELD_TIMES_AUGMENT}, {ProjectItem.FIELD_TIMES_PREPRO}'
        )
        item = response.get('Item', None)
        print(item)
        if item is None:
            project_rec = None
        else:
            project_rec = ProjectItem(item)

        return project_rec
