import numpy as np

import boto3
import traceback
from typing import List, Optional, Dict, Tuple
import cv2

# import preprocessing_list  # Import to register all preprocessing
CodeToPreprocess: Dict[str, str] = {
    # "PRE-000": "auto_orientation",
    # "PRE-001": "grayscale",
    "PRE-002": "normalize_brightness",
    "PRE-003": "normalize_hue",
    "PRE-004": "normalize_saturation",
    "PRE-005": "normalize_sharpness",
    "PRE-006": "normalize_contrast",
    # "PRE-007": "normalize_affine",
    "PRE-008": "equalize_histogram",
    # "PRE-009": "high_resolution",
    # "PRE-010": "detect_outlier",
    # "PRE-011": "tilling",
    # "PRE-012": "cropping",
}

from references import (
    find_reference_brightness_image,
    find_reference_hue_image,
    find_reference_saturation_image,
    find_reference_signal_to_noise_image,
)


class S3Downloader:
    s3 = boto3.client("s3")

    @staticmethod
    def split_s3_path(path: str) -> Tuple[str, str]:
        """
        Split s3 path into bucket and file name
        >>> split_s3_uri('s3://bucket/folder/image.png')
        ('bucket', 'folder/image.png')
        """
        # s3_path, file_name = os.path.split
        bucket, _, file_name = path.replace("s3://", "").partition("/")
        return bucket, file_name

    def read_image(uri: str) -> np.ndarray:
        try:
            bucket, file_name = S3Downloader.split_s3_path(uri)
            s3_response_object = S3Downloader.s3.get_object(
                Bucket=bucket, Key=file_name
            )

            array: np.ndarray = np.frombuffer(
                s3_response_object["Body"].read(), np.uint8
            )
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image

        except S3Downloader.s3.exceptions.NoSuchKey:
            message: str = f"File not found. [bucket={bucket},key={file_name}]"
            print(message)
            raise Exception(message)

        except S3Downloader.s3.exceptions.NoSuchBucket:
            message: str = f"Bucket not found. [bucket={bucket},key={file_name}]"
            print(message)
            raise Exception(message)


def calculate_resolution(image):
    height, width, channels = image.shape
    return width, height


def read_image(image_path: str, max_width=4000, max_height=4000) -> np.ndarray:
    if "s3://" in image_path:  # image in S3 bucket
        image: np.ndarray = S3Downloader.read_image(image_path)
    else:  # image in local machine
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    width, height = calculate_resolution(image)
    print(f"resolution of image: {image_path} is (wxh) \n {(width, height)}")
    if width > max_width or height > max_height:
        return None

    return np.ascontiguousarray(image)


class Preprocessor:
    def __init__(self, use_gpu: bool = False, max_width=400, max_height=4000):
        """
        Apply random augmentations on batch of images.

        Parameters:
        -----------
        use_gpu:
            Whether to perform augmentations on gpu or not. Default: False
        """
        self.use_gpu: bool = use_gpu
        self.max_width = max_width
        self.max_height = max_height

    def get_reference_image_paths(
        self,
        data: List[Tuple[str, str]],
        preprocess_codes: List[str],
    ) -> Dict[str, str]:
        # Mapping from a preprocess_code to its corresponding reference image path
        reference_paths_dict: Dict[str, tuple] = {}

        ### Read all input images beforehand and filter the oversize image
        input_images: List[str] = []
        overlimit_images: List[str] = []
        input_images_path_update: List[str] = []
        data_update = []
        for sub_data in data:
            if "s3://" not in sub_data["s3_key"]:
                input_image_path = f's3://{sub_data["s3_key"]}'
            else:
                input_image_path = sub_data["s3_key"]

            value = read_image(input_image_path, self.max_width, self.max_height)
            if value is None:
                overlimit_images.append(input_image_path)
            else:
                input_images.append(value)
                input_images_path_update.append(input_image_path)
                data_update.append(sub_data)

        ### Find reference image for each preprocessing code
        for code in preprocess_codes:
            if CodeToPreprocess.get(code, None) is None:
                continue
            preprocess_name: str = CodeToPreprocess[code]
            reference_paths_dict[code] = self.__find_reference_image_path(
                input_images, input_images_path_update, preprocess_name
            )

        print("reference_paths_dict after calculate reference: ", reference_paths_dict)
        return reference_paths_dict, data_update, overlimit_images

    def __find_reference_image_path(
        self,
        input_images: List[np.ndarray],
        input_image_paths: List[str],
        preprocess_name: str,
    ) -> str:
        type_choose_index = "median"
        if preprocess_name == "normalize_brightness":
            reference_ls_value: List[float] = find_reference_brightness_image(
                input_images, input_image_paths
            )
        elif preprocess_name == "normalize_hue":
            reference_ls_value = find_reference_hue_image(
                input_images, input_image_paths
            )
        elif preprocess_name == "normalize_saturation":
            reference_ls_value = find_reference_saturation_image(
                input_images, input_image_paths
            )
        else:
            reference_ls_value = find_reference_signal_to_noise_image(
                input_images, input_image_paths
            )
            type_choose_index = "sorted"

        return reference_ls_value, type_choose_index
