import boto3
import json
import os

from config import *
from response import *
from error_messages import *
from identity_check import *
client_events = boto3.client('events')  
@error_response
def lambda_handler(event, context):
    body = json.loads(event['body'])
    try :
       identity_id, task_id =body['identity_id'], body['task_id']
    except Exception as e:
        print(e)
        return generate_response(
            message=MESS_INVALID_JSON_INPUT,
            data={},
            headers=RESPONSE_HEADER,
            error = True
        )
    data = {
        'identity_id':identity_id, 'task_id':task_id
    }
    client_events.put_events(
                        Entries=[
                            {
                                'Source': 'source.events',
                                'DetailType': 'lambda.event',
                                'Detail': json.dumps(data),
                                'EventBusName': os.environ["EVENT_BUS_NAME"]
                            },
                        ]
                    )
    return generate_response(
            message="OK",
            status_code=HTTPStatus.OK,
            data={})