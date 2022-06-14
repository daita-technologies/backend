import os
import boto3
import time
import json
import shutil
import logging
import time
from zipfile import ZipFile
from datetime import datetime
from pathlib import Path
from botocore.client import Config
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError


EFS_ROOT = os.getenv("EFSMountPath")
TableDataFlowTaskName = os.getenv("TableDataFlowTaskName")
TableMethodsName = os.getenv("TableMethodsName")
bucket_name = os.getenv("S3BucketName")
s3 = boto3.client('s3')
VALUE_TASK_FINISH = "FINISH"

# config for uploading zipfile to s3
MULTIPART_THRESHOLD = 1
MULTIPART_CONCURRENCY = 2
MAX_RETRY_COUNT = 3


log = logging.getLogger('s3_uploader')


def convert_current_date_to_iso8601():
    my_date = datetime.now()
    return my_date.isoformat()


def convert_method_name(dict_method, ls_method_id_str):
    """
    convert generation method id to method string name
    """
    print("ls_method_id_str: ", ls_method_id_str)
    if type(ls_method_id_str) is str:
        ls_method_id_str = ls_method_id_str.replace(']', '').replace('[', '').replace("'", "")
        if len(ls_method_id_str) == 0:
            return ""

        ls_method_id = ls_method_id_str.split(",")
    else:
        ls_method_id = ls_method_id_str

    # print("ls_methof_id: ", ls_method_id)
    ls_method_id_convert = [dict_method.get(x.strip(), "") for x in ls_method_id]
    str_final = ",".join(ls_method_id_convert)

    return str_final

def upload_progress_db(status, identity_id, task_id, presign_url, s3_key):
    db_resource = boto3.resource("dynamodb")
    table = db_resource.Table(TableDataFlowTaskName)
    table.update_item(
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

def download(
    down_type,
    project_name,
    workdir,
    identity_id,
    project_id, task_id):
    try:
        db_resource = boto3.resource("dynamodb")

        ## get all methods
        table = db_resource.Table(TableMethodsName)
        response = table.scan()
        dict_method = {}
        for item in response["Items"]:
            dict_method[item["method_id"]] = item["method_name"]
        # print("dict_method: \n", dict_method)

        # dowload and zip
        starttime = time.time()

        workdir = Path(EFS_ROOT, workdir)
        zip_dir = Path(EFS_ROOT)
        zip_dir.mkdir(parents=True, exist_ok=True)
        zipfile_name = f"{project_name}_{down_type}_{task_id}.zip"
        zip_path = zip_dir.joinpath(zipfile_name)
        json_object = {}

        files_ = set(workdir.glob("**/*")) - set(workdir.glob("**/*.json"))
        image_files = [f for f in files_ if f.is_file()]
        with ZipFile(zip_path, 'w') as zip:
            for file_ in image_files:
                with file_.with_suffix(".json").open() as rstr:
                    file_info = json.load(rstr)
                type_method = file_info["type_method"]
                # print("result: ", result)
                zip.write(file_, f"{type_method}/{file_.name}")
                json_object[file_info["filename"]] = {
                    "name": file_info["filename"],
                    "typeOfImage": file_info["type_method"],
                    "class": file_info.get("classtype", ""),
                    "methodToCreate": convert_method_name(dict_method, file_info.get("gen_id", "")),
                    "size": int(file_info.get("size", 0)),
                    "nameOfProject": project_name
                }

            # write this object to json file
            json_filename = f"{project_name}_{down_type}_{str(int(time.time()))}.json"
            filepath = workdir.joinpath(json_filename)
            with filepath.open('w') as wstr:
                json.dump(json_object, wstr)

            # write to zip file
            zip.write(filepath, json_filename)
        endtime_down_zip = time.time()

        # put to s3
        key_name = os.path.join(identity_id, project_id, "download", zipfile_name)
        put_zip_to_s3(str(zip_path), bucket_name, key_name)
        endtime_put_s3 = time.time()

        # delete data in EFS
        os.remove(zip_path)
        shutil.rmtree(workdir)

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


def lambda_handler(event, context):
    task_id = event["task_id"]
    identity_id = event["identity_id"]
    down_type = event["down_type"]
    project_name = event["project_name"]
    project_id = event["project_id"]
    workdir = event["taskresult"]["workdir"]

    url, s3_key = download(down_type, project_name, workdir, identity_id, project_id, task_id)
    upload_progress_db(VALUE_TASK_FINISH, identity_id, task_id, url, s3_key)
    print(url, s3_key)
