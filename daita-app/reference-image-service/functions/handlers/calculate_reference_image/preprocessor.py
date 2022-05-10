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
            s3_response_object = S3Downloader.s3.get_object(Bucket=bucket, Key=file_name)

            array: np.ndarray = np.frombuffer(s3_response_object["Body"].read(), np.uint8)
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

def read_image(image_path: str) -> np.ndarray:
    if "s3://" in image_path:  # image in S3 bucket
        image: np.ndarray = S3Downloader.read_image(image_path)
    else:  # image in local machine
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return np.ascontiguousarray(image)

class Preprocessor:
    def __init__(self, use_gpu: bool = False):
        """
        Apply random augmentations on batch of images.

        Parameters:
        -----------
        use_gpu:
            Whether to perform augmentations on gpu or not. Default: False
        """
        self.use_gpu: bool = use_gpu        

    def get_reference_image_paths(self,
                                  data: List[Tuple[str, str]],
                                  preprocess_codes: List[str],
                                  ) -> Dict[str, str]:
        # Mapping from a preprocess_code to its corresponding reference image path
        reference_paths_dict: Dict[str, tuple] = {}

        input_image_paths = [f's3://{x["s3_key"]}' for x in data]
        print("Inputs s3_key_path: ", input_image_paths)

        # Read all input images beforehand
        input_images: List[str] = [
            read_image(input_image_path)
            for input_image_path in input_image_paths
        ]
        # Find reference image for each preprocessing code
        for code in preprocess_codes:
            if CodeToPreprocess.get(code, None) is None:
                continue
            preprocess_name: str = CodeToPreprocess[code]
            reference_paths_dict[code] = self.__find_reference_image_path(
                input_images,
                input_image_paths,
                preprocess_name
            )
        
        print("reference_paths_dict after calculate reference: ", reference_paths_dict)
        return reference_paths_dict    

    def __find_reference_image_path(self,
                                    input_images: List[np.ndarray],
                                    input_image_paths: List[str],
                                    preprocess_name: str
                                    ) -> str:
        type_choose_index = "median"
        if preprocess_name == "normalize_brightness":
            reference_ls_value: List[float] = find_reference_brightness_image(input_images, input_image_paths)
        elif preprocess_name == "normalize_hue":
            reference_ls_value = find_reference_hue_image(input_images, input_image_paths)
        elif preprocess_name == "normalize_saturation":
            reference_ls_value = find_reference_saturation_image(input_images, input_image_paths)
        else:
            reference_ls_value = find_reference_signal_to_noise_image(input_images, input_image_paths)
            type_choose_index = "sorted"

        return reference_ls_value, type_choose_index
    