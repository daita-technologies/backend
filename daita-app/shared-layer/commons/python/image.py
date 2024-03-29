import boto3
import random
from datetime import datetime
from utils import convert_current_date_to_iso8601
from identity_check import aws_get_identity_id
TBL_data_original = 'data_original'
TBL_data_proprocess= 'data_preprocess'
TBL_PROJECT = 'projects'
MAX_NUMBER_GEN_PER_IMAGES = 5

def dydb_update_project_data_type_number(db_resource, identity_id, project_name, data_type, data_number, times_generated):
    try:
        table = db_resource.Table(TBL_PROJECT)
        response = table.update_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ExpressionAttributeNames= {
                '#DA_TY': data_type
            },
            ExpressionAttributeValues = {
                ':va':  data_number,
                ':da': convert_current_date_to_iso8601(),
                ':tg': times_generated
            },
            UpdateExpression = 'SET #DA_TY = :va , updated_date = :da, times_generated = :tg' 
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise 
    if response.get('Item', None):
        return response['Item']        
    return None

def dydb_get_project(db_resource, identity_id, project_name):
    try:
        table = db_resource.Table(TBL_PROJECT)
        response = table.get_item(
            Key={
                'identity_id': identity_id,
                'project_name': project_name,
            },
            ProjectionExpression= 'project_id, s3_prefix, times_generated'
        )
    except Exception as e:
        print('Error: ', repr(e))
        raise 
    if response.get('Item', None):
        return response['Item']        
    return None
def dydb_update_class_data(table, project_id, filename, classtype):
    response = table.update_item(
            Key={
                'project_id': project_id,
                'filename': filename,
            },
            ExpressionAttributeNames= {
                '#CT': 'classtype',
            },
            ExpressionAttributeValues = {
                ':ct':  classtype,
                
            },
            UpdateExpression = 'SET #CT = :ct' 
        )

class ImageLoader(object):
    def __init__(self):
        self.db_resource = boto3.resource('dynamodb')  
    '''
    info_image:
                identity_id 
                project_id 
                augment_code
                data_number
                data_type
                project_name
    '''
    def __call__(self,info_image):
        identity_id = info_image['identity_id']
        project_id = info_image['project_id']
        ls_methods_id =  info_image['augment_code']
        project_name = info_image['project_name']
        data_type = info_image['data_type']
        data_number = info_image['data_number']
        # get type of process
        type_method = 'PREPROCESS'
        if 'AUG' in ls_methods_id[0]:
            type_method = 'AUGMENT'
        elif 'PRE' in ls_methods_id[0]:
            type_method = 'PREPROCESS'
        else:
            raise(Exception('list method is not valid!'))
        infor = dydb_get_project(self.db_resource, identity_id, project_name)
        s3_prefix = infor['s3_prefix']
        
        if data_type == 'ORIGINAL':
            table_name = TBL_data_original
        elif data_type == 'PREPROCESS':
            table_name = TBL_data_proprocess
        else:
            raise(Exception('data_type is not valid!'))
            
        if type_method == 'PREPROCESS':
            table_name = TBL_data_original
            
        # get list data
        table = self.db_resource.Table(table_name)
        response = table.query(
                KeyConditionExpression = Key('project_id').eq(project_id),
                ProjectionExpression='filename, s3_key',
            )
        ls_data = response['Items']
        
        if type_method == 'PREPROCESS':
            ls_process = [item['s3_key'] for item in ls_data] # use all data in original for preprocessing
        elif type_method == 'AUGMENT':
            random.shuffle(ls_data)
            ls_process = []
            ls_train = []
            ls_val = []
            ls_test = []
            for idx, data in enumerate(ls_data):
                if idx<data_number[0]:
                    ls_train.append(data)
                    ls_process.append(data['s3_key'])
                    classtype = 'TRAIN'
                elif idx<data_number[0]+data_number[1]:
                    ls_val.append(data)
                    classtype = 'VAL'
                else:
                    ls_test.append(data)
                    classtype = 'TEST'
                    
                dydb_update_class_data(table, project_id, data["filename"], classtype)
        return {"images": ls_process, "project_prefix":s3_prefix},None    