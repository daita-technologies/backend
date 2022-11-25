import boto3
import json
import os
import uuid

from config import *
from response import *
from error_messages import *
from utils import convert_current_date_to_iso8601, aws_get_identity_id, get_num_prj
import const


from lambda_base_class import LambdaBaseClass
from boto3.dynamodb.conditions import Key, Attr

table = boto3.client('dynamodb')
cognito_client = boto3.client('cognito-idp')

class SendEmailIdentityIDClass(LambdaBaseClass):

    def __init__(self) -> None:   
        super().__init__()     

    @LambdaBaseClass.parse_body
    def parser(self, body):
        self.logger.debug(f"body in main_parser: {body}")

        self.identity_id = body["identity_id"]
        self.message_email = body["message_email"]
        self.message_email_text = body["message_email_text"]

    def _check_input_value(self): 
        return     

    def get_mail_User(self, identity_id):
        resq = table.scan(TableName=self.env.TABLE_USER,
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
            response = cognito_client.list_users(UserPoolId = self.env.USER_POOL_ID,
                                                     AttributesToGet = ['email'],
                                                     Filter=f'sub=\"{ID_User}\"'
                                                )
            print("response list cognito user: \n", response)
            if len(response['Users']) > 0:
                user_cognito = response['Users'][0]
                mail = user_cognito['Attributes'][0]['Value']
                return mail

        return None

    def send_mail(self, mail, message_email, message_email_text):
        client = boto3.client("ses")
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
        
        return

    def handle(self, event, context):
        print(event)
        ### parse body
        self.parser(event)

        email = self.get_mail_User(self.identity_id)
        self.send_mail(email, self.message_email, self.message_email_text)

        return 


@error_response
def lambda_handler(event, context):

    return SendEmailIdentityIDClass().handle(event, context)