import json
import boto3
import hashlib
import hmac
import base64
import os
from utils import convert_response, aws_get_identity_id


MAX_NUMBER_ITEM_QUERY = 1000
MAX_NUM_IMAGES_IN_ORIGINAL = 1000


def lambda_handler(event, context):

    # process input body
    try:
        print(event['body'])
        body = json.loads(event['body'])
        id_token = body["id_token"]
        project_id = body["project_id"]
        ls_filename = body["ls_filename"]

        # check quantiy of items
        if len(ls_filename) > MAX_NUMBER_ITEM_QUERY:
            raise Exception(
                f'The number of items is over {MAX_NUMBER_ITEM_QUERY}')

        # create the batch request from input data
        ls_batch_request = []
        for object in ls_filename:
            request = {
                'project_id': {'S': project_id},  # partition key
                'filename': {'S': object}
            }
            ls_batch_request.append(request)

    except Exception as e:
        return convert_response({"error": True,
                                 "success": False,
                                 "message": repr(e),
                                 "data": None})

    # get identity_id from id token, also check the authentication from client
    try:
        identity_id = aws_get_identity_id(id_token)
    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True,
                                 "success": False,
                                 "message": repr(e),
                                 "data": None})

    # query data from DB
    try:
        db_client = boto3.client('dynamodb')
        ls_data = []
        start_idx = 0
        while start_idx < len(ls_batch_request):
            next_idx = start_idx + 50
            response = db_client.batch_get_item(
                RequestItems={
                    os.environ["T_DATA_ORI"]: {
                        'Keys': ls_batch_request[start_idx:next_idx],
                        'ProjectionExpression': 'filename, size'
                    }
                }
            )
            start_idx = next_idx
            print(start_idx, next_idx)
            for data in response['Responses'][os.environ["T_DATA_ORI"]]:
                ls_data.append(
                    {'filename': data['filename']['S'], 'size': data['size']['N']})

        print(ls_data)

        # check available image is over the limitation
        db_resource = boto3.resource("dynamodb")
        table = db_resource.Table(os.environ["T_PROJECT_SUMMARY"])
        response = table.get_item(
            Key={
                "project_id": project_id,
                "type": "ORIGINAL"
            }
        )
        if response.get('Item'):
            current_num_data = response['Item'].get('count', 0)
        else:
            current_num_data = 0
        if len(ls_batch_request)-len(ls_data)+current_num_data > MAX_NUM_IMAGES_IN_ORIGINAL:
            raise(Exception(
                f'The number of images in original of project is over the limitation {MAX_NUM_IMAGES_IN_ORIGINAL}!'))

    except Exception as e:
        print('Error: ', repr(e))
        return convert_response({"error": True,
                                 "success": False,
                                 "message": repr(e),
                                 "data": None})

    return convert_response({
        'data': ls_data,
        "error": False,
        "success": True,
        "message": None
    })
