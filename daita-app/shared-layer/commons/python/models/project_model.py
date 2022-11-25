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
    FIELD_REFERENCE_IMAGES      = KEY_NAME_REFERENCE_IMAGES
    FIELD_DATANUM_ORIGINAL      = VALUE_TYPE_DATA_ORIGINAL
    FIELD_DATANUM_PREPROCESS    = VALUE_TYPE_DATA_PREPROCESSED
    FIELD_AUG_PARAMETERS        = KEY_NAME_AUG_PARAMS

    def __init__(self, dict_info) -> None:        
        print("start init")
        for key, value in dict_info.items():
            self.__dict__[key]=value
        print("init success: ", self.__dict__)

    def get_value_w_default(self, name, default_value=None):
        if self.__dict__.get(name, None):
            return self.__dict__[name]
        else:
            self.__dict__[name] = default_value
            return default_value


class ProjectModel():
    def __init__(self, table_name) -> None:
        self.table = boto3.resource('dynamodb').Table(table_name)               
   
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

    def update_project_generate_times(self, identity_id, project_name, times_augment, times_preprocess,
                                     reference_images, aug_params):
        response = self.table.update_item(
            Key={
                ProjectItem.FIELD_IDENTITY_ID: identity_id,
                ProjectItem.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#P_T': ProjectItem.FIELD_TIMES_PREPRO,
                '#A_T': ProjectItem.FIELD_TIMES_AUGMENT,
                '#UP_DATE': ProjectItem.FIELD_UPDATE_DATE,
                "#RE_IM": ProjectItem.FIELD_REFERENCE_IMAGES,
                "#AU_PA": ProjectItem.FIELD_AUG_PARAMETERS
            },
            ExpressionAttributeValues = {
                ':vp_t': times_preprocess,
                ':va_t': times_augment,
                ':da': convert_current_date_to_iso8601(),   
                ':re_im': reference_images,
                ':au_pa': aug_params
            },
            UpdateExpression = 'SET #P_T = :vp_t , #A_T = :va_t, #AU_PA = :au_pa, #UP_DATE = :da, #RE_IM = :re_im'
        )

        return

    def update_generate_expert_mode_param(self, identity_id, project_name, reference_images, aug_params):
        response = self.table.update_item(
            Key={
                ProjectItem.FIELD_IDENTITY_ID: identity_id,
                ProjectItem.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#UP_DATE': ProjectItem.FIELD_UPDATE_DATE,
                "#RE_IM": ProjectItem.FIELD_REFERENCE_IMAGES,
                "#AU_PA": ProjectItem.FIELD_AUG_PARAMETERS
            },
            ExpressionAttributeValues = {
                ':da': convert_current_date_to_iso8601(),   
                ':re_im': reference_images,
                ':au_pa': aug_params
            },
            UpdateExpression = 'SET #AU_PA = :au_pa, #UP_DATE = :da, #RE_IM = :re_im'
        )

        return

    def update_project_reference_images(self, identity_id, project_name, reference_images):
        """
        update project reference images after finish calculate reference images with ls_method choosen by client
        """
        response = self.table.update_item(
            Key={
                ProjectItem.FIELD_IDENTITY_ID: identity_id,
                ProjectItem.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#UP_DATE': ProjectItem.FIELD_UPDATE_DATE,
                "#RE_IM": ProjectItem.FIELD_REFERENCE_IMAGES,
            },
            ExpressionAttributeValues = {
                ':da': convert_current_date_to_iso8601(),   
                ':re_im': reference_images,
            },
            UpdateExpression = 'SET #RE_IM = :re_im, #UP_DATE = :da'
        )

        return

    def put_item_w_condition(self, item, condition):
        self.table.put_item(
                    Item = item,
                    ConditionExpression = condition
                )
        return
