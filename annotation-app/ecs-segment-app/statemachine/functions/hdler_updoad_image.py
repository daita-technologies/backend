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

def send_mail(mail, project_name):
    client = boto3.client("ses")
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
    print("send email to: ", mail)
    response = client.send_email(
        Destination={
            "ToAddresses": [mail],
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": "UTF-8",
                    "Data": message_email,
                },
                "Text": {
                    "Charset": "UTF-8",
                    "Data": message_email_text,
                },
            },
            "Subject": {
                "Charset": "UTF-8",
                "Data": "Your AI detection results are ready",
            },
        },
        Source="DAITA Team <hello@daita.tech>",
    )

def get_mail_User(identity_id):
    resq = table.scan(TableName=os.environ['TABLE_USER'],
    FilterExpression='#id = :id',
    ExpressionAttributeNames=
                    {
                        '#id':'identity_id'
                    } ,
    ExpressionAttributeValues={
        ':id':{'S':identity_id}
    })

    userInfo =  resq['Items']

    print("User info: ", userInfo)
    if len(userInfo) > 0:
        ID_User = userInfo[0]['ID']['S']
        response = client.list_users(UserPoolId=os.environ['USERPOOL'],AttributesToGet = ['email'],Filter=f'sub=\"{ID_User}\"')
        print("response list cognito user: \n", response)
        if len(response['Users']) > 0:
            user_cognito = response['Users'][0]
            mail = user_cognito['Attributes'][0]['Value']
            return mail
    return None




def check_finish(project_id):
    total, finish = model_data.query_progress_ai_segm(project_id)

    if total == finish and total != 0:
        # get identity id 
        projectResponse = model_project.find_project_by_project_ID(project_id)
        identity_id = projectResponse['identity_id']
        project_name = projectResponse['project_name']
        mail = get_mail_User(identity_id)
        if mail != None:
            send_mail(mail,project_name)


@error_response
def lambda_handler(event, context):
    output_folder = os.path.join(event['input_folder'],'output')
    output_folder = os.path.join(os.environ['EFSPATH'],output_folder)
    
    for index , it in enumerate(event['records']):
        with open(os.path.join(output_folder,str(index)+'.json'),'r') as f:
            s3_key = upload_segmentation_s3(f.read(),s3_key=it['s3_key'])
            update_s3_gen(it['project_id'], it['filename'],s3_key)
            check_finish(it['project_id'])
    return {}