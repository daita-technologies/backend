import boto3
from boto3.dynamodb.conditions import Key, Attr
from config import *
from utils import *




class AnnoProjectModel():
    FIELD_IDENTITY_ID           = "identity_id"
    FIELD_PROJECT_ID            = "project_id"
    FIELD_PROJECT_NAME          = "project_name"
    FIELD_GEN_STATUS            = "gen_status"     ### status of generating progress
    FIELD_S3_PREFIX             = "s3_prefix"
    FIELD_S3_LABEL              = "s3_label"
    FIELD_S3_PRJ_ROOT           = "s3_prj_root"
    FIELD_IS_SAMPLE             = "is_sample"
    FIELD_PROJECT_INFO          = "project_info"
    FIELD_TIMES_AUGMENT         = "times_generated"
    FIELD_TIMES_PREPRO          = "times_propr"
    FIELD_UPDATE_DATE           = "updated_date"
    FIELD_CREATED_DATE          = "created_date"
    FIELD_LINKED_PROJECT        = "link_daita_prj_id"
    FIELD_CATEGORY_DEFAULT      = "defa_category_id"    ### the default category of project, remove it after has category logic
    FIELD_REFERENCE_IMAGES      = KEY_NAME_REFERENCE_IMAGES
    FIELD_DATANUM_ORIGINAL      = VALUE_TYPE_DATA_ORIGINAL
    FIELD_DATANUM_PREPROCESS    = VALUE_TYPE_DATA_PREPROCESSED
    FIELD_AUG_PARAMETERS        = KEY_NAME_AUG_PARAMS

    VALUE_GEN_STATUS_GENERATING = "GENERATING"
    VALUE_GEN_STATUS_FINISH     = "FINISH"

    def __init__(self, table_name) -> None:
        print("table name: ", table_name)
        self.table = boto3.resource('dynamodb').Table(table_name)     

    def get_all_project(self, identity_id):

        ls_fields_projection = [self.FIELD_PROJECT_ID, self.FIELD_PROJECT_NAME, 
                                self.FIELD_GEN_STATUS, self.FIELD_CREATED_DATE]

        response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                ProjectionExpression= ",".join(ls_fields_projection),
        )
        ls_items = response.get("Items", [])

        while 'LastEvaluatedKey' in response:
            next_token = response['LastEvaluatedKey']
            response = self.table.query (
                KeyConditionExpression=Key(self.FIELD_IDENTITY_ID).eq(identity_id),
                ProjectionExpression = ",".join(ls_fields_projection),
                ExclusiveStartKey=next_token
            )

            ls_items += response.get("Items", [])

        return ls_items          
   
    def get_project_info(self, identity_id, project_name, ls_projection_fields = []) -> dict:      
        ### set default fields for projection      
        if len(ls_projection_fields) == 0:
            ls_projection_fields = [self.FIELD_PROJECT_ID, self.FIELD_PROJECT_NAME, self.FIELD_GEN_STATUS]

        ### query
        response = self.table.get_item(
            Key={
                self.FIELD_IDENTITY_ID: identity_id,
                self.FIELD_PROJECT_NAME: project_name,
            },
            ProjectionExpression= ",".join(ls_projection_fields)
        )
        item = response.get('Item', None)
        print(item)
        
        return item

    def update_project_info(self, identity_id, project_name, data_type, data_number):        
        response = self.table.update_item(
            Key={
                self.FIELD_IDENTITY_ID: identity_id,
                self.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#DA_TY': data_type,
                '#UP_DATE': self.FIELD_UPDATE_DATE
            },
            ExpressionAttributeValues = {
                ':va':  data_number,
                ':da': convert_current_date_to_iso8601(),                
            },
            UpdateExpression = 'SET #DA_TY = :va , #UP_DATE = :da'
        )

        return

    def update_project_gen_status(self, identity_id, project_name, status):
        response = self.table.update_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ExpressionAttributeValues={
                ':st': status,
            },
            UpdateExpression='SET  gen_status = :st'
        )

        return

    def update_project_gen_status_category_default(self, identity_id, project_name, status, category_id):
        response = self.table.update_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ExpressionAttributeValues={
                ':st': status,
                ':cat': category_id,
                ':up': convert_current_date_to_iso8601()
            },
            ExpressionAttributeNames= {
                '#GEN': self.FIELD_GEN_STATUS,
                '#CAT': self.FIELD_CATEGORY_DEFAULT,
                '#UP': self.FIELD_UPDATE_DATE,
            },
            UpdateExpression='SET  #GEN = :st, #CAT = :cat, #UP = :up'
        )

        return

    # def update_project_attributes(self, identity_id, project_name, ls_attributes_info):
    #     """
    #     update the attributes of project in general input parameters, the update expression default will be set

    #     params:
    #     - ls_attributes_info: should be in format [[<attr_name_1>, <value_1>], [<attr_name_2>, <value_2>], ...]
    #     """
    #     ex_attri_name = {}
    #     ex_value = {}
    #     ls_update_ex = []
    #     for name, value in ls_attributes_info:
    #         ex_attri_name


    def update_project_generate_times(self, identity_id, project_name, times_augment, times_preprocess,
                                     reference_images, aug_params):
        response = self.table.update_item(
            Key={
                self.FIELD_IDENTITY_ID: identity_id,
                self.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#P_T': self.FIELD_TIMES_PREPRO,
                '#A_T': self.FIELD_TIMES_AUGMENT,
                '#UP_DATE': self.FIELD_UPDATE_DATE,
                "#RE_IM": self.FIELD_REFERENCE_IMAGES,
                "#AU_PA": self.FIELD_AUG_PARAMETERS
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
                self.FIELD_IDENTITY_ID: identity_id,
                self.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#UP_DATE': self.FIELD_UPDATE_DATE,
                "#RE_IM": self.FIELD_REFERENCE_IMAGES,
                "#AU_PA": self.FIELD_AUG_PARAMETERS
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
                self.FIELD_IDENTITY_ID: identity_id,
                self.FIELD_PROJECT_NAME: project_name,
            },
            ExpressionAttributeNames= {
                '#UP_DATE': self.FIELD_UPDATE_DATE,
                "#RE_IM": self.FIELD_REFERENCE_IMAGES,
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
