import json
import base64

import boto3


client = boto3.client('ses')


def get_email(id_token):
    header, payload, signature = id_token.split(".")
    user_info = json.loads(base64.b64decode(payload + "="*10)) #add missing padding
    return user_info["email"]


def lambda_handler(event, context):
    email = get_email(event["id_token"])
    print("send mail")
    #TODO: change href to something for meaningful
    message = f"<p>Hi,</p><p>Your files are ready for download, check them out <a href='https://demo.daita.tech'>here</a>. <p>Cheers,</p> <p>The DAITA Team</p>"
    response = client.send_email(
        Destination={
            'ToAddresses':[
                email
            ],
        },
        Message={
            'Subject':{
                    'Charset':'UTF-8',
                    'Data':"You're files are ready for download"
            },
            'Body':{
                'Html':{
                    'Charset':'UTF-8',
                    'Data': message,

                },
                'Text':{
                    'Charset':'UTF-8',
                    'Data':"You're files is ready for download"
                }

            },
        },
        Source="DAITA Team <noreply@daita.tech>",

    )
    return {
        "error": False,
        "success":True,
        "message": "Email sent! Message ID: {}".format(response['MessageId']),
        "data": None
    }
