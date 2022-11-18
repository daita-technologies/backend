import boto3
import re
import os
import json
from response import *

from lambda_base_class import LambdaBaseClass
from models.annotaition.anno_data_model import AnnoDataModel
from models.annotaition.anno_project_model import AnnoProjectModel
table = boto3.client('dynamodb')
s3 = boto3.client('s3')
model_data = AnnoDataModel(os.environ['TABLE_ANNOTATION_ORIGIN'])
model_project = AnnoProjectModel(os.environ['TABLE_ANNOTATION_PROJECT'])
client = boto3.client('cognito-idp')

def update_s3_gen(project_id, filename, s3_key_gen):
    response = table.update_item(
                TableName=os.environ["TABLE_ANNOTATION_ORIGIN"],
                Key={
                    'project_id': {
                        'S': project_id
                    },
                    'filename': {
                        'S': filename
                    }
                },
                ExpressionAttributeNames={
                  '#gen': 's3_key_segm',
                },
                ExpressionAttributeValues={
                  ':gen':{
                    'S': s3_key_gen
                  }
                },
                UpdateExpression='SET #gen = :gen',
            )
    print(f'Response ',response)

def upload_segmentation_s3(data,s3_key):
    dirfilename =  os.path.dirname(s3_key)
    dirfilename = dirfilename.replace('raw_data','clone_project')
    basename =  os.path.splitext(os.path.basename(s3_key))[0] + '_segment.json'
    filename = os.path.join(dirfilename, basename)
    bucket =  filename.split('/')[0]
    key = '/'.join(filename.split('/')[1:])
    s3.put_object(
                    Body=data,
                    Bucket=bucket ,
                    Key= key
                )
    return filename

def send_mail(identity_id, project_name):
    message_email = """
    <p>Dear User,</p>
    <p>Your AI detection task is completed. Please log into DAITA Platform and go to <a href='https://app.daita.tech/annotation/project/{}'>Annotation</a> to access your results.</p>
    <p>Best,</p>
    <p>The DAITA Team</p>
    <p>---</p>
    <p><i>In case you encounter any issues or questions, please contact us at <a href="mailto:contact@daita.tech">contact@daita.tech</a>.</i></p>
    """.format(
        project_name
    )
    message_email_text = """
    Dear User,
    Your AI detection task is completed. Please log into DAITA Platform and go to https://app.daita.tech/annotation/project/{} to access your results
    Best,
    The DAITA Team
    In case you encounter any issues or questions, please contact us at contact@daita.tech.
    """.format(
        project_name
    )

    print("send email to identityid: ", identity_id)

    # response = invoke_lambda_func(os.environ["FUNC_SEND_EMAIL_IDENTITY_NAME"],
    #                                 {
    #                                     "identity_id": identity_id,
    #                                     "message_email": message_email,
    #                                     "message_email_text": message_email_text
    #                                 })
    
    return  {
                "identity_id": identity_id,
                "message_email": message_email,
                "message_email_text": message_email_text
    }

def invoke_lambda_func(function_name, body_info, type_request="RequestResponse"):
    lambdaInvokeClient = boto3.client('lambda')
    print("invoke function name: ", function_name)
    lambdaInvokeReq = lambdaInvokeClient.invoke(
        FunctionName=function_name,
        Payload=json.dumps({'body': body_info}),
        InvocationType=type_request,
    )

    return lambdaInvokeReq['Payload'].read()

def check_finish(project_id):
    total, finish = model_data.query_progress_ai_segm(project_id)

    if total == finish and total != 0:
        # get identity id 
        ls_projectResponse = model_project.find_project_by_project_ID(project_id)
        if len(ls_projectResponse)>0:
            projectResponse = ls_projectResponse[0]
            identity_id = projectResponse['identity_id']
            project_name = projectResponse['project_name']     
            return send_mail(identity_id, project_name)
    return None 


@error_response
def lambda_handler(event, context):
    output_folder = os.path.join(event['input_folder'],'output')
    output_folder = os.path.join(os.environ['EFSPATH'],output_folder)

    print(event['records'])
    result = {'data':[]}
    for index , it in enumerate(event['records']):
        with open(os.path.join(output_folder,str(index)+'.json'),'r') as f:
            s3_key = upload_segmentation_s3(f.read(),s3_key=it['s3_key'])
            update_s3_gen(it['project_id'], it['filename'],s3_key)
            response = check_finish(it['project_id'])
            if response  != None:
                result['data'].append(response)
    return result