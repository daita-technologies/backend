import json
import boto3
import base64
import random
import aws_encryption_sdk
import botocore.credentials
import botocore.session
from aws_encryption_sdk.identifiers import CommitmentPolicy

generatorKeyId = 'arn:aws:kms:us-east-2:737589818430:alias/descript-confirm-code'
keyIds = ['arn:aws:kms:us-east-2:737589818430:key/b338cc1b-dc7f-4118-97da-230d1ce199be']

kms_kwargs = dict(key_ids=keyIds)
sess = botocore.session.get_session()
sess._credentials = botocore.credentials.Credentials(
    access_key='AKIA2XO6HOQ7IMN62R43', secret_key='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')
kms_kwargs["botocore_session"] = sess
encryption_client = aws_encryption_sdk.EncryptionSDKClient(
    commitment_policy=CommitmentPolicy.REQUIRE_ENCRYPT_ALLOW_DECRYPT
)
kms_key_provider = aws_encryption_sdk.StrictAwsKmsMasterKeyProvider(**kms_kwargs)

class EventID(object):
    def __init__(self):
        self.db_client = boto3.resource('dynamodb',region_name="us-east-2",aws_access_key_id="AKIA2XO6HOQ7IMN62R43",aws_secret_access_key="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")
    def create_item(self,eventID,type):
        self.db_client.Table("eventUser").put_item(Item = {
            'event_ID':eventID,
            'type': type
        })
    
    def Is_check_item_exist(self,eventID,type):
        response = self.db_client.Table("eventUser").get_item(
              Key={
                   'event_ID':eventID,
                   'type': type
              }
        )
        return True if 'Item' in response else False



def invoke_sendmail_cognito_service(subject,destination_email,message_email):
    client = boto3.client('lambda')
    payload_json = None 
    try :
        response = client.invoke(
                FunctionName="staging-sendmail-cognito-service",
                InvocationType="RequestResponse",
                Payload=json.dumps({"subject":subject,"destination_email":destination_email,"message_email":message_email})
            )
        payload_json = json.loads(response['Payload'].read())
    except Exception as e:
        return None , e
    
    return payload_json , None 


def lambda_handler(event, context):
    eventDB = EventID()
    print(context.aws_request_id)
    print(event['request'])
    print( event['request']['code'])
    print(event['triggerSource'] )
    ciphertext = base64.b64decode(event['request']['code'])
    decrypted_plaintext, _  = encryption_client.decrypt(
       source=ciphertext,key_provider=kms_key_provider
    )
    plainTextCode = decrypted_plaintext.decode('utf-8')
    print(plainTextCode)
    execute = False
    if not eventDB.Is_check_item_exist(context.aws_request_id,event['triggerSource']):
        execute = True
        eventDB.create_item(context.aws_request_id,event['triggerSource'])
    print("Is execute ",execute)
    email = event['request']['userAttributes']['email']
    if execute and event['triggerSource'] in ['CustomEmailSender_ForgotPassword']:
        message_email = "<p>Your confirmation code is {}</p>".format(plainTextCode)
        data , err =  invoke_sendmail_cognito_service("Your email confirmation code",email,message_email)
    return 
