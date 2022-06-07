import os
import re
import json
import random
import glob
import boto3
from .logging_api import logDebug
from itertools import chain, islice

# from .utils import batcher

"""
S3 : download image
"""


def is_json(file_check):
    return os.path.splitext(os.path.basename(file_check))[1] in [".json"]


def batcher(iterable, size):
    iterator = iter(iterable)
    for first in iterator:
        yield list(chain([first], islice(iterator, size - 1)))


class S3(object):
    def __init__(self, project_prefix, process_type):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=os.environ["ACCESSKEYID"],
            aws_secret_access_key=os.environ["SECRET_KEY"],
        )
        self.bucket = None
        self.s3_key = None
        self.project_prefix = project_prefix
        self.bucket, self.folder = self.split(self.project_prefix)
        self.prefix_pwd = "/home/ec2-user"
        self.process_type = process_type

    def split(self, uri):
        if not "s3" in uri:
            temp = uri.split("/")
            bucket = temp[0]
            filename = "/".join([temp[i] for i in range(1, len(temp))])
        else:
            match = re.match(r"s3:\/\/(.+?)\/(.+)", uri)
            bucket = match.group(1)
            filename = match.group(2)
        return bucket, filename

    def download(self, uri, folder):
        bucket, filename = self.split(uri)
        basename = os.path.basename(filename)
        new_image = os.path.join(folder, basename)
        self.s3.download_file(bucket, filename, new_image)

    def download_images(self, images, list_name_aug, folder):

        raw_images_dir = os.path.join(folder, "raw_images")
        gen_images_dir = os.path.join(folder, "gen_images")
        input_dir = os.path.join("/home/ec2-user/efs", raw_images_dir)
        output_dir = os.path.join("/home/ec2-user/efs", gen_images_dir)
        os.makedirs(input_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        for it in images:
            self.download(it, input_dir)
        list_image = list(
            map(
                lambda x: x.replace("/home/ec2-user", ""),
                list(glob.glob(input_dir + "/**")),
            )
        )

        def generator():
            yield from list_image

        batch_size = 2
        batch_input = []
        batch_output = []
        total_len = 0

        for index, batch in enumerate(batcher(generator(), batch_size)):
            output_dir_temp = output_dir
            total_len += len(batch)
            batch_input.append(batch)
            nameoutput = os.path.join(output_dir_temp, str(index))
            os.makedirs(nameoutput, exist_ok=True)
            batch_output.append(nameoutput.replace("/home/ec2-user", ""))

        info = {
            "images_download": len(list_image),
            "batch_input": batch_input,
            "batch_output": batch_output,
            "batch_size": batch_size,
        }
        return info

    def upload_image(
        self,
        project_prefix,
        database_method,
        process_type,
        list_aug,
        output_dir,
        total_file,
    ):
        info = []
        bucket, folder = self.split(project_prefix)
        pwd = output_dir
        logDebug.debug("[DEBUG] PWD {}".format(pwd))
        img_list = []
        # check enough image
        while True:
            for r, d, f in os.walk(pwd):
                for file in f:
                    img_list.append(os.path.join(r, file))
            cur_length_file = (
                len(list(filter(is_json, img_list)))
                if process_type == "AUGMENT"
                else len(img_list)
            )
            logDebug.debug(
                "[DEBUG] cur_length_file {} total {} \n".format(
                    cur_length_file, total_file
                )
            )
            logDebug.debug("[DEBUG] image_list :{}\n".format(img_list))
            if cur_length_file == total_file:
                break
            else:
                img_list = []

        for it_img in img_list:
            logDebug.debug("[DEBUG] img_list {}\n".format(it_img))
            temp_namefile = os.path.basename(it_img)
            s3_namefile = os.path.join(folder, temp_namefile)
            aug_code = []  #

            if not "json" in it_img and process_type == "AUGMENT":
                file_json = os.path.splitext(it_img)[0] + ".json"
                logDebug.debug("[DEBUF] upload Json{}".format(file_json))
                with open(file_json) as f:
                    data = json.load(f)
                    logDebug.info("[INFO] json data aug: {}".format(data))

                    if (
                        "augment_name" in data
                        and data["augment_name"] in database_method
                    ):
                        aug_code.append(database_method[data["augment_name"]])
            else:
                aug_code = list_aug

            logDebug.debug("[DEBUG] upload File{}".format(it_img))
            # updaload image to S3 , not json
            if not "json" in it_img:
                info.append(
                    {
                        "filename": s3_namefile,
                        "size": os.path.getsize(it_img),
                        "gen_id": str(aug_code),
                    }
                )
                with open(it_img, "rb") as f:
                    self.s3.put_object(Bucket=bucket, Key=s3_namefile, Body=f)
        new_key_s3 = project_prefix
        return new_key_s3, info
