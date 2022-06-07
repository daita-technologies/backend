import os
import glob
import time
import threading
import requests
import json
import boto3
import redis
from .s3 import S3, batcher
from .logging_api import logInfo, logError, logDebug
from celery import shared_task
from celery.result import AsyncResult

conn = redis.Redis(host="localhost", port=6379, db=0)
EXPIRED = 60 * 32 + 30
# request to service to notice task is finish
def request_finish_task_ec2(ec2_id, task_id):
    client = boto3.client("lambda")
    try:
        response = client.invoke(
            FunctionName="staging-balancer-asy-finish-task",
            InvocationType="RequestResponse",
            Payload=json.dumps({"ec2_id": ec2_id, "task_id": task_id}),
        )
        logDebug.debug(
            "[DEBUG]staging-balancer-asy-finish-task: {}".format(
                json.loads(response["Payload"].read())
            )
        )
    except Exception as e:
        print(e)
        logError.error("[ERROR]staging-balancer-asy-finish-task: {}".format(e))


def is_img(img):
    return not os.path.splitext(img)[1] in [".json"]


def get_number_files(output_dir):
    img_list = []
    for r, d, f in os.walk(output_dir):
        for file in f:
            img_list.append(os.path.join(r, file))
    img_list = list(filter(is_img, img_list))
    return len(img_list)


def insert_KV_EC2(ec2_id, task_id):
    pipline = conn.pipeline()
    pipline.lpush(ec2_id, task_id)
    pipline.execute()
    conn.set("instanceKey:" + ec2_id, "EX", EXPIRED)


def done_task_ec2(ec2_id, task_id):
    for i in range(0, conn.llen(ec2_id)):
        logInfo.info("[INFO] ec2_id {} : {}".format(ec2_id, conn.lindex(ec2_id, i)))
    conn.lrem(ec2_id, 0, task_id)
    request_finish_task_ec2(ec2_id, task_id)


def request_update_proj(update_pro_info, list_file_s3):
    batch_list_s3 = list(batcher(list_file_s3, 20))
    for batch_file in batch_list_s3:
        logDebug.debug("[DEBUG] batch file {}".format(batch_file))
        info = {
            "identity_id": update_pro_info["identity_id"],
            "id_token": update_pro_info["id_token"],
            "project_id": update_pro_info["project_id"],
            "project_name": update_pro_info["project_name"],
            "type_method": update_pro_info["process_type"],
            "ls_object_info": [],
        }
        for info_file in batch_file:
            filename = os.path.basename(info_file["filename"])
            info["ls_object_info"].append(
                {
                    "s3_key": os.path.join(update_pro_info["s3_key"], filename),
                    "filename": filename,
                    "hash": "",
                    "size": info_file["size"],
                    "is_ori": False,
                    "gen_id": info_file["gen_id"],
                }
            )
        logDebug.debug("[DEBUG] Log Request Update Upload : {}\n".format(info))
        try:
            update_project_output = requests.post(
                "https://4cujdvfmd4.execute-api.us-east-2.amazonaws.com/staging/projects/upload_update",
                json=info,
            )
            if update_project_output.status_code != 200:
                raise Exception(update_project_output.text)
            update_project_output = update_project_output.json()
        except Exception as e:
            raise ("ERROR Update project output : " + str(e))
        logDebug.debug(
            "[DEBUG] Request Update Upload: {}\n".format(update_project_output)
        )


class ThreadRequest(threading.Thread):
    def __init__(self, worker):
        threading.Thread.__init__(self)
        self.worker = worker

    """
    """

    def run(self):
        while True:
            input_list, output_dir = self.worker["in_queue"].get()
            if self.worker["process_type"] == "AUGMENT":
                input_json = {
                    "images_paths": input_list,
                    "output_folder": output_dir,
                    "num_augments_per_image": self.worker["num_augments_per_image"],
                    "codes": [],
                    "type": "augmentation",
                }
            else:
                input_json = {
                    "images_paths": input_list,
                    "output_folder": output_dir,
                    "type": "preprocessing",
                    "codes": [],
                }
            self.worker["log_request_AI"].put(
                "Host {} input_json : {}".format(self.worker["host"], input_json)
            )
            self.worker["log_request_AI"].task_done()

            request_task = request_AI_task.apply_async(
                queue="request_ai",
                kwargs={"host": self.worker["host"], "input_json": input_json},
            )
            while not request_task.successful():
                time.sleep(1)

            data = request_task.get()

            if "Error_retry" in data:
                self.worker["error_message_queue"].put("Error_retry")

            logInfo.info("[INFO] Request AI reponse {}".format(data))
            self.worker["in_queue"].task_done()


"""
input_uploading_image <dictionary>:
                                output_dir : <list> : diretory of gen image 
                                info_request :<dictionary> :    id_token :
                                                                project_id : 
                                                                project_name
                                                                project_name
                                                                identity_id
                                process_type :<string>: AUGMENT or PREPROCESS
                                aug : <list>
                                # error_message_queue : <queue>: put error message into queue to log
                                total_file <int> : the image numbers generate
"""


def uploading_image(input_uploading_image):
    s3_instance = S3(
        input_uploading_image["project_prefix"], input_uploading_image["process_type"]
    )
    s3_key, s3_info = s3_instance.upload_image(
        input_uploading_image["project_prefix"],
        input_uploading_image["method_db"],
        input_uploading_image["process_type"],
        input_uploading_image["list_aug"],
        input_uploading_image["output_dir"],
        input_uploading_image["total_file"],
    )
    update_pro_info = {
        "id_token": input_uploading_image["info_request"]["id_token"],
        "project_id": input_uploading_image["info_request"]["project_id"],
        "project_name": input_uploading_image["info_request"]["project_name"],
        "s3_key": s3_key,
        "identity_id": input_uploading_image["info_request"]["identity_id"],
        "process_type": input_uploading_image["process_type"],
    }
    try:
        request_update_proj(update_pro_info, s3_info)
    except Exception as e:
        raise Exception("request update project {}".format(e))


@shared_task(
    bind=True,
    retries=1,
    autoretry_for=(Exception,),
    exponential_backoff=2,
    retry_backoff=True,
    retry_jitter=False,
    default_retry_delay=1,
    max_retries=15,
)
def request_AI_task(self, host, input_json):
    logInfo.info(
        "[INFO] The time Retry {} max retries : {} \n".format(
            self.request.retries, self.max_retries
        )
    )
    if self.request.retries >= self.max_retries:
        logError.error(
            "[ERROR] MAX RETRIES Request Max Retry : {} , Retry times : {} \n".format(
                self.max_retries, self.request.retries
            )
        )
        return {"Error_retry": "error"}
    try:
        outputs = requests.post(host, json=input_json)
    except Exception as e:
        logError.error("[ERROR] request AI: {}".format(input_json))
        raise Exception(e)
    # check enough image

    total_image = (
        input_json["num_augments_per_image"] * len(input_json["images_paths"])
        if "num_augments_per_image" in input_json
        else len(input_json["images_paths"])
    )
    ## if the task get enough image but response status code is 500
    if get_number_files(input_json["output_folder"]) == total_image:
        return {"message": "enough"}

    if outputs.status_code == 500:
        logError.error("[ERROR] Request AI error : {}".format(outputs.text))
        raise Exception(outputs.text)

    return outputs.json()
