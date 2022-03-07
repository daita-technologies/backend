import os
import boto3
import time
import json
from zipfile import ZipFile
import shutil
from botocore.client import Config
from boto3.dynamodb.conditions import Key, Attr
from concurrent import futures
from datetime import datetime
import logging
from pathlib import Path
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
import time



relative_path = '/mnt/efs/images'
os.makedirs(relative_path, exist_ok=True)
bucket_name = 'daita-client-data' 
s3 = boto3.client('s3')   

IDENTITY_POOL_ID =   'us-east-2:fa0b76bc-01fa-4bb8-b7cf-a5000954aafb' #'us-east-2:639788f0-a9b0-460d-9f50-23bbe5bc7140'
USER_POOL_ID = 'us-east-2_ZbwpnYN4g'   #'us-east-2_6Sc8AZij7'

# max_workers = 5
# self.abs_path = os.path.abspath(relative_path)
MAX_WORKERS = 8

# config for uploading zipfile to s3
MULTIPART_THRESHOLD = 1
MULTIPART_CONCURRENCY = 2
MAX_RETRY_COUNT = 3


log = logging.getLogger('s3_uploader')

def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()
 
def fetch(info):
    abs_path = os.path.abspath(relative_path)
    key = info["s3_key"]
    type_method = info["type_method"]

    folder = os.path.split(key)[0]
    filename = os.path.split(key)[1]
    file = f'{abs_path}/{folder}/{type_method}/{filename}'
    os.makedirs(os.path.split(file)[0], exist_ok=True)  

    key = key.replace(f'{bucket_name}/', "")
    # print('key request: ', key)
    with open(file, 'wb') as data:
        s3.download_fileobj(bucket_name, key, data)

    return (file, f'{type_method}/{filename}', info)

def fetch_all(keys):
    print("fetch_all")
    with futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_key = {executor.submit(fetch, key): key for key in keys}

        print("All URLs submitted.")

        for future in futures.as_completed(future_to_key):
            key = future_to_key[future]
            exception = future.exception()

            if not exception:
                yield key, future.result()
            else:
                yield key, exception

def get_all_file_paths(directory):  
    # initializing empty file paths list
    file_paths = []

    # crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full filepath.
            filepath = os.path.join(root, filename)
            file_paths.append(filepath)

    # returning all file paths
    return file_paths

def aws_get_identity_id(id_token):
   
    identity_client = boto3.client('cognito-identity')
    PROVIDER = f'cognito-idp.{identity_client.meta.region_name}.amazonaws.com/{USER_POOL_ID}'

    try:
        identity_response = identity_client.get_id(
                            IdentityPoolId=IDENTITY_POOL_ID, 
                            Logins = {PROVIDER: id_token})
    except Exception as e:
        print('Error: ', repr(e))
        raise Exception("Id_token is invalid!")

    identity_id = identity_response['IdentityId']

    return identity_id

def convert_method_name(dict_method, ls_method_id_str):
    """
    convert generation method id to method string name
    """
    ls_method_id_str = ls_method_id_str.replace(']', '').replace('[', '').replace("'", "")
    if len(ls_method_id_str) == 0:
        return ""
    
    ls_method_id = ls_method_id_str.split(",")
    # print("ls_methof_id: ", ls_method_id)
    str_final = ""
    for method_id in ls_method_id:
        # print(f"method_id: {method_id.strip()}, method_name: {dict_method[method_id.strip()]}")
        str_final += f'{dict_method.get(method_id.strip(), "")}, '        
    # print("string final: ", str_final)

    return str_final

def upload_progress_db(status, identity_id, task_id, presign_url, s3_key):
    db_resource = boto3.resource("dynamodb")
    table = db_resource.Table('down_tasks')
    response = table.update_item(
                    Key={
                        'identity_id': identity_id,
                        'task_id': task_id,
                    }, 
                    ExpressionAttributeNames= {
                        '#ST': "status"
                    },                   
                    ExpressionAttributeValues = {
                        ':da': convert_current_date_to_iso8601(),
                        ":ke": s3_key,
                        ":ur": presign_url,
                        ":st": status
                    },
                    UpdateExpression = 'SET s3_key = :ke, presign_url = :ur, #ST = :st, updated_date = :da'
                )
    return

def put_zip_to_s3(filepath, bucket_name, key_name, metadata=None):
    """
    Upload zipfile to s3 and process with multipart and multi thread setting
    """
    log.info("Uploading [" + filepath + "] to [" + bucket_name + "] bucket ...")
    log.info("S3 path: [ s3://" + bucket_name + "/" + key_name + " ]")
    # Multipart transfers occur when the file size exceeds the value of the multipart_threshold attribute
    if not Path(filepath).is_file:
        log.error("File [" + filepath + "] does not exist!")
        raise Exception("File not found!")
 
    if key_name is None:
        log.error("object_path is null!")
        raise Exception("S3 object must be set!")
 
    GB = 1024 ** 3
    mp_threshold = MULTIPART_THRESHOLD*GB
    concurrency = MULTIPART_CONCURRENCY
    transfer_config = TransferConfig(multipart_threshold=mp_threshold, use_threads=True, max_concurrency=concurrency)
 
    login_attempt = False
    retry = MAX_RETRY_COUNT
     
    while retry > 0:
        try:
            s3.upload_file(filepath, bucket_name, key_name, Config=transfer_config, ExtraArgs=metadata)
            
            log.info("File [" + filepath + "] uploaded successfully")
            retry = 0
         
        except ClientError as e:
            log.error("Failed to upload object!")
            log.exception(e)
            if e.response['Error']['Code'] == 'ExpiredToken':
                log.warning('Login token expired')
                retry -= 1
                log.debug("retry = " + str(retry))                
            else:
                log.error("Unhandled error code:")
                log.debug(e.response['Error']['Code'])
                raise Exception("Error")
 
        except boto3.exceptions.S3UploadFailedError as e:
            log.error("Failed to upload object!")
            log.exception(e)
            if 'ExpiredToken' in str(e):
                log.warning('Login token expired')
                log.info("Handling...")
                retry -= 1
                log.debug("retry = " + str(retry))
            else:
                log.error("Unknown error!")
                raise Exception("Error")
 
        except Exception as e:
            log.error("Unknown exception occured!")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(e).__name__, e.args)
            log.debug(message)
            log.exception(e)
            raise Exception("Error")

def download(data):   
    try:
        # id_token: str = data["id_token"]
        down_type: str = data["down_type"]   # ALL, augment, preprocess, original
        project_name: str = data["project_name"]
        project_id: str = data["project_id"]

        # project_name = 'Driving Dataset Sample'
        # project_id = 'Driving Dataset Sample_c64bd36f28a84897ad77b598046bfbd1'
        # print("call aws get_identity: ", id_token)
        # identity_id = aws_get_identity_id(id_token)        
        # print(identity_id)

        # get list key of the project
        db_resource = boto3.resource("dynamodb")

        ls_table = []
        if down_type == "ALL":
            ls_table.append(db_resource.Table('data_original'))
            ls_table.append(db_resource.Table('data_augment'))
            ls_table.append(db_resource.Table('data_preprocess'))
        elif down_type == "ORIGINAL":
            ls_table.append(db_resource.Table('data_original'))
        elif down_type == "PREPROCESS":
            ls_table.append(db_resource.Table('data_preprocess'))
        elif down_type == "AUGMENT":
            ls_table.append(db_resource.Table('data_augment'))
        else:
            return "Error"
            # return Response(
            #     status_code=500,
            #     content=f"Field 'down_type' must be ALL | ORIGINAL | PREPROCESS | AUGMENT. Got type={down_type}"
            # )

        ## get all dowloaded object information from DB
        ls_object = []
        for table in ls_table:                
            response = table.query(
                    KeyConditionExpression = Key('project_id').eq(project_id),
                    ProjectionExpression='filename, s3_key, classtype, gen_id, type_method, size',
                    Limit = 500
                )
            ls_object = ls_object + response['Items']
            # print("total len response: ", len(response['Items']))
            next_token = response.get('LastEvaluatedKey', None)
            while next_token is not None:
                response = table.query(
                    KeyConditionExpression = Key('project_id').eq(project_id),
                    ProjectionExpression='filename, s3_key, classtype, gen_id, type_method, size',
                    Limit = 500,
                    ExclusiveStartKey=next_token,
                )
                next_token = response.get('LastEvaluatedKey', None)
                # print("total len response next: ", len(response['Items']))
                ls_object = ls_object + response['Items']

        ## get all methods
        table = db_resource.Table('methods')
        response = table.scan()
        dict_method = {}
        for item in response["Items"]:
            dict_method[item["method_id"]] = item["method_name"]
        # print("dict_method: \n", dict_method)
        

        if len(ls_object) == 0:
            return {"s3_key": None}
        print("Final len: ", len(ls_object))
        
        # setup dir
        folder_s3 = ls_object[0]['s3_key'].replace(f'{bucket_name}/', "").replace(f"/{ls_object[0]['filename']}", "")
        delete_dir = ls_object[0]['s3_key'].replace(f"/{ls_object[0]['filename']}", "")


        # dowload and zip
        starttime = time.time()
        zipfile_name = f"{project_name}_{down_type}.zip"
        zip_dir = f"/mnt/efs/zip"
        os.makedirs(zip_dir, exist_ok=True) 
        zip_path = os.path.join(zip_dir, zipfile_name)
        json_object = {}
        with ZipFile(zip_path,'w') as zip:
            for key, result in fetch_all(ls_object):
                # print("result: ", result)
                zip.write(result[0], result[1])
                json_object[result[2]["filename"]] = {
                    "name": result[2]["filename"],
                    "typeOfImage": result[2]["type_method"],
                    "class": result[2].get("classtype", ""),
                    "methodToCreate": convert_method_name(dict_method, result[2].get("gen_id", "")),
                    "size": int(result[2].get("size", 0)),
                    "nameOfProject": project_name
                }

            # write this object to json file
            json_filename = f"{project_name}_{down_type}_{str(int(time.time()))}.json"
            dir_path = f'{relative_path}/{delete_dir}'
            filepath = os.path.join(dir_path, json_filename)
            with open(filepath, 'w') as outfile:
                json.dump(json_object, outfile)

            # write to zip file
            zip.write(filepath, f"{json_filename}")   
        endtime_down_zip = time.time()    
  
            
        
        # put to s3            
        key_name = f"{folder_s3}/download/{zipfile_name}"
        put_zip_to_s3(zip_path, bucket_name, key_name)
        endtime_put_s3 = time.time()        


        # delete data in EFS
        dir_path = f'{relative_path}/{delete_dir}'
        print("delete dir path: ", dir_path)
        try:
            shutil.rmtree(dir_path)
        except OSError as e:
            print("Error: %s : %s" % (dir_path, e.strerror))

        # get presign url for this zip file:
        s3_conf = boto3.client('s3', config=Config(signature_version='s3v4'))
        url = s3_conf.generate_presigned_url(
            ClientMethod='get_object',
            Params={
                'Bucket': bucket_name,
                'Key': key_name
            },
            ExpiresIn=1*60*60
        )
        
        print(f"Processing time of down_zip: {endtime_down_zip-starttime}  puts3: {endtime_put_s3-endtime_down_zip}")
                
        return  url, key_name
    except Exception as e:
        print("error")
        print(e)        
        raise Exception("Error!")