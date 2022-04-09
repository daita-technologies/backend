import numpy as np
import cv2
import boto3

import os
from typing import Tuple

from registry import register_healthcheck
from healthcheck_utils import S3
from healthcheck_utils import (
    calculate_contrast_score,
    calculate_signal_to_noise,
    calculate_sharpness_score,
    calculate_luminance,
)


@register_healthcheck(name="signal_to_noise")
def check_signal_to_noise_RGB(image: np.ndarray, **kwargs) -> Tuple[float, float, float]:
    R, G, B = cv2.split(image)
    snr_R: float = calculate_signal_to_noise(R)
    snr_G: float = calculate_signal_to_noise(G)
    snr_B: float = calculate_signal_to_noise(B)
    return (snr_R, snr_G, snr_B)


@register_healthcheck(name="sharpness")
def check_sharpness(image: np.ndarray, **kwargs) -> float:
    sharpness: float = calculate_sharpness_score(image)
    return sharpness


@register_healthcheck(name="contrast")
def check_contrast(image: np.ndarray, **kwargs) -> float:
    contrast: float = calculate_contrast_score(image)
    return contrast


@register_healthcheck(name="luminance")
def check_luminance(image: np.ndarray, **kwargs) -> int:
    luminance: float = calculate_luminance(image)
    return luminance


@register_healthcheck(name="file_size")
def check_file_size(image: np.ndarray, **kwargs) -> int:
    image_path: str = kwargs["image_path"]
    if "s3://" in image_path:  # path is an S3 URI
        bucket, key_name = S3.split_s3_path(image_path)
        file_size_in_bytes: int = boto3.resource('s3').Bucket(bucket).Object(key_name).content_length
    else:  # local path
        file_size_in_bytes = os.path.getsize(image_path)

    file_size_in_mb: int = file_size_in_bytes / 1024 / 1024
    return file_size_in_mb


@register_healthcheck(name="height_width_aspect_ratio")
def check_image_height_and_width(image: np.ndarray, **kwargs) -> Tuple[int, int, float]:
    height, width = image.shape[:2]
    aspect_ratio: float = height / width
    return (height, width, aspect_ratio)


@register_healthcheck(name="mean_red_channel")
def check_mean_red_channel(image: np.ndarray, **kwargs) -> int:
    R, _, _ = cv2.split(image)
    mean = np.mean(R)
    return mean


@register_healthcheck(name="mean_green_channel")
def check_mean_green_channel(image: np.ndarray, **kwargs) -> int:
    _, G, _ = cv2.split(image)
    mean = np.mean(G)
    return mean


@register_healthcheck(name="mean_blue_channel")
def check_mean_blue_channel(image: np.ndarray, **kwargs) -> int:
    _, _, B = cv2.split(image)
    mean = np.mean(B)
    return mean


@register_healthcheck(name="extension")
def check_extension(image: np.ndarray, **kwargs) -> str:
    image_path: str = kwargs["image_path"]
    _, extension = os.path.splitext(image_path)
    return extension.lower()