import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *



class ProjectItem():
    FIELD_IDENTITY_ID           = "identity_id"
    FIELD_PROJECT_ID            = "project_id"
    FIELD_PROJECT_NAME          = "project_name"
    FIELD_GEN_STATUS            = "gen_status"
    FIELD_S3_PREFIX             = "s3_prefix"
    FIELD_IS_SAMPLE             = "is_sample"
    FIELD_PROJECT_INFO          = "project_info"
    FIELD_TIMES_AUGMENT         = "times_generated"
    FIELD_TIMES_PREPRO          = "times_propr"
    FIELD_UPDATE_DATE           = "updated_date"
    FIELD_DATANUM_ORIGINAL      = VALUE_TYPE_DATA_ORIGINAL
    FIELD_DATANUM_PREPROCESS    = VALUE_TYPE_DATA_PREPROCESSED

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

    def update_project_info(self, identity_id, project_name, data_type, data_number):        
        response = self.table.update_item(
            Key={
                ProjectItem.FIELD_IDENTITY_ID: identity_id,
                ProjectItem.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#DA_TY': data_type,
                '#UP_DATE': ProjectItem.FIELD_UPDATE_DATE
            },
            ExpressionAttributeValues = {
                ':va':  data_number,
                ':da': convert_current_date_to_iso8601(),                
            },
            UpdateExpression = 'SET #DA_TY = :va , #UP_DATE = :da'
        )

        return

    def update_project_generate_times(self, identity_id, project_name, times_augment, times_preprocess):
        response = self.table.update_item(
            Key={
                ProjectItem.FIELD_IDENTITY_ID: identity_id,
                ProjectItem.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#P_T': ProjectItem.FIELD_TIMES_PREPRO,
                '#A_T': ProjectItem.FIELD_TIMES_AUGMENT,
                '#UP_DATE': ProjectItem.FIELD_UPDATE_DATE
            },
            ExpressionAttributeValues = {
                ':vp_t': times_preprocess,
                ':va_t': times_augment,
                ':da': convert_current_date_to_iso8601(),                
            },
            UpdateExpression = 'SET #P_T = :vp_t , #A_T = :va_t, #UP_DATE = :da'
        )

        return
