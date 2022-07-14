import requests
import time
from config import *
from response import *
from utils import *
from identity_check import *
calculateReferencesImagesApi = f'{URL}/reference_image/calculate'
statusReferencesImagesApi = f'{URL}/reference_image/status'
infoReferencecesImagesAPi = f'{URL}/reference_image/info'


@error_response
def lambda_handler(event, context):
    if 'process_type' in event and event['process_type'] != 'PREPROCESS':
        event['is_retry'] = False
        return event
    if bool(event['reference_images']):
        event['is_retry'] = False
        return event
    if not 'reference_image_task_id' in event:
        reponseCalRefImage = requests.post(calculateReferencesImagesApi, json={
            'id_token': event['id_token'],
            'project_id': event['project_id'],
            'ls_method_client_choose': [],
            'project_name': event['project_name']
        })
        if reponseCalRefImage.status_code == 200:
            data = reponseCalRefImage.json()
            event['reference_image_task_id'] = data['data']['task_id']
            print(data)

    start = time.time()

    while time.time() - start <= 120:
        reponseStatusRefImage = requests.post(statusReferencesImagesApi, json={
            'id_token': event['id_token'],
            'task_id': event['reference_image_task_id'],
        })
        data = reponseStatusRefImage.json()['data']
        if data['status'] == 'FINISH':
            reponseInfoRefImage = requests.post(infoReferencecesImagesAPi, json={
                'project_id': event['project_id'],
                'id_token': event['id_token'],
            })
            info = reponseInfoRefImage.json()['data']
            for it in info:
                event['reference_images'][it['method_id']
                                          ] = "s3://{}".format(it['image_s3_path'])
                event['is_retry'] = False
        else:
            event['is_retry'] = True
        time.sleep(5)
    print(event)
    return event
