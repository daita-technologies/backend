import cv2
import boto3
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Union
from skimage.color import rgb2ycbcr
from skimage.color import rgb2lab


def is_gray_image(image: np.ndarray) -> bool:
    if image.ndim == 2 or (image.ndim == 3 and image.shape[2] == 1):
        return True
    return False


def get_current_time() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def read_image(image_path: str, is_from_s3 = False) -> np.ndarray:
    if is_from_s3:  
        # image in S3 bucket
        if "s3://" not in image_path:
            image_path = "s3://" + image_path
        image: np.ndarray = S3.read_image(image_path)
    else:  # image in local machine
        image = cv2.imread(image_path, cv2.IMREAD_COLOR)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return np.ascontiguousarray(image)


def save_image(image_path: str, image: np.ndarray) -> None:
    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(image_path, image)
    
def calculate_contrast_score(image: np.ndarray) -> float:
    """
    https://en.wikipedia.org/wiki/Contrast_(vision)#Michelson_contrast
    """
    YCrCb: torch.Tensor = rgb2ycbcr(image)
    Y = YCrCb[0, :, :]

    min = np.min(Y)
    max = np.max(Y)

    # compute contrast
    contrast = (max - min) / (max + min)
    return float(contrast)


def calculate_sharpness_score(image: np.ndarray) -> float:
    sharpness: float = cv2.Laplacian(image, cv2.CV_16S).std()
    return sharpness


def calculate_signal_to_noise(image: np.ndarray, axis=None, ddof=0) -> float:
    """
    The signal-to-noise ratio of the input data.
    Returns the signal-to-noise ratio of an image, here defined as the mean
    divided by the standard deviation.
    Parameters
    ----------
    a : array_like
        An array_like object containing the sample data.
    axis : int or None, optional
        Axis along which to operate. If None, compute over
        the whole image.
    ddof : int, optional
        Degrees of freedom correction for standard deviation. Default is 0.
    Returns
    -------
    s2n : ndarray
        The mean to standard deviation ratio(s) along `axis`, or 0 where the
        standard deviation is 0.
    """
    image = np.asanyarray(image)
    mean = image.mean(axis)
    std = image.std(axis=axis, ddof=ddof)
    signal_to_noise: np.ndarray = np.where(std == 0, 0, mean / std)
    return float(signal_to_noise)


def calculate_luminance(image: np.ndarray) -> float:
    lab: float = rgb2lab(image)
    luminance: int = cv2.Laplacian(lab, cv2.CV_64F).std()
    return luminance


class S3:
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
            bucket, file_name = S3.split_s3_path(uri)
            s3_response_object = S3.s3.get_object(Bucket=bucket, Key=file_name)

            array: np.ndarray = np.frombuffer(s3_response_object["Body"].read(), np.uint8)
            image = cv2.imdecode(array, cv2.IMREAD_COLOR)
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return image

        except S3.s3.exceptions.NoSuchKey:
            message: str = f"File not found. [bucket={bucket},key={file_name}]"
            print(message)
            raise Exception(message)

        except S3.s3.exceptions.NoSuchBucket:
            message: str = f"Bucket not found. [bucket={bucket},key={file_name}]"
            print(message)
            raise Exception(message)