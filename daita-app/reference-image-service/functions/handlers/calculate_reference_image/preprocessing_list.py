# import numpy as np
# from typing import Dict, Any, Tuple

# from utils import resize_image
# from preprocessing.base import BasePreprocessing
# from preprocessing.registry import register_preprocessing
# from preprocessing.preprocessing_utils import (
#     calculate_contrast_score,
#     calculate_sharpness_score,
# )


# @register_preprocessing(name="auto_orientation")
# class RotateExif(BasePreprocessing):
#     def __init__(self):
#         pass

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Rotate image according to metadata in EXIF.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         image_path
#             Path to input image

#         Returns
#         ------
#         tensor images of shape [B, C, H, W]
#         """
#         from PIL import Image, ExifTags
#         from scipy.ndimage import rotate

#         is_normalized: bool = False
#         image_path: str = kwargs["image_path"]
#         image_pil: Image.Image = Image.open(image_path)

#         if image_pil._getexif() is not None:
#             exif: Dict[str, Any] = {
#                 ExifTags.TAGS[k]: v
#                 for k, v in image_pil._getexif().items()
#                 if k in ExifTags.TAGS
#             }

#             if "orientation" in exif:
#                 orientation: int = exif["orientation"]
#                 is_normalized = True

#                 if orientation == 1:
#                     image_out = image
#                 elif orientation == 2:
#                     image_out = np.fliplr(image)
#                 elif orientation == 3:
#                     image_out = np.flipud(image)
#                 elif orientation == 4:
#                     image_out = np.fliplr(image)
#                     image_out = np.flipud(image_out)
#                 elif orientation == 5:
#                     image_out = rotate(image, angle=-90)
#                     image_out = np.fliplr(image_out)
#                 elif orientation == 6:
#                     image_out = rotate(image, angle=-90)
#                 elif orientation == 7:
#                     image_out = rotate(image, angle=90)
#                     image_out = np.fliplr(image_out)
#                 elif orientation == 8:
#                     image_out = rotate(image, angle=90)
#                 return image_out, is_normalized

#         return image, is_normalized


# @register_preprocessing(name="grayscale")
# class Grayscale(BasePreprocessing):
#     def __init__(self):
#         pass

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Normalize brightness of a tensor image given a reference image.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         Return
#         ------
#         normalized tensor images of shape [B, C, H, W]
#         """
#         from skimage.color import rgb2gray

#         is_normalized: bool = True
#         image_out: np.ndarray = rgb2gray(image)
#         return image_out, is_normalized


# @register_preprocessing(name="normalize_brightness")
# class NormalizeBrightness(BasePreprocessing):
#     def __init__(self):
#         pass

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Normalize brightness of a tensor image given a reference image.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         Return
#         ------
#         normalized tensor images of shape [B, C, H, W]
#         """
#         from skimage.color import rgb2hsv, hsv2rgb
#         from skimage.exposure import match_histograms

#         is_normalized: bool = False

#         reference_image_hsv: np.ndarray = rgb2hsv(reference_image)
#         reference_brightness: float = reference_image_hsv[:, :, 2].var()

#         image_hsv: np.ndarray = rgb2hsv(image)
#         brightness: float = image_hsv[:, :, 2].var()

#         if abs(brightness - reference_brightness) / reference_brightness > 0.75:
#             matched_hsv = match_histograms(image_hsv, reference_image_hsv, multichannel=True)
#             image_hsv[2] = matched_hsv[2]
#             image_out = (hsv2rgb(image_hsv) * 255).astype(np.uint8)
#             is_normalized = True
#             return image_out, is_normalized

#         return image, is_normalized


# @register_preprocessing(name="normalize_hue")
# class NormalizeHue(BasePreprocessing):
#     def __init__(self):
#         pass

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Normalize hue of a tensor image given a reference image.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         Return
#         ------
#         normalized tensor images of shape [B, C, H, W]
#         """
#         from skimage.color import rgb2hsv, hsv2rgb
#         from skimage.exposure import match_histograms

#         is_normalized: bool = False

#         reference_image_hsv: np.ndarray = rgb2hsv(reference_image)
#         reference_hue: float = reference_image_hsv[:, :, 0].var()

#         image_hsv: np.ndarray = rgb2hsv(image)
#         hue: float = image_hsv[:, :, 0].var()

#         if abs(hue - reference_hue) / reference_hue > 0.75:
#             matched_hsv = match_histograms(image_hsv, reference_image_hsv, multichannel=True)
#             image_hsv[0] = matched_hsv[0]

#             image_out = (hsv2rgb(image_hsv) * 255).astype(np.uint8)
#             is_normalized = True
#             return image_out, is_normalized

#         return image, is_normalized


# @register_preprocessing(name="normalize_saturation")
# class NormalizeSaturation(BasePreprocessing):
#     def __init__(self):
#         pass

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Normalize hue of a tensor image given a reference image.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         Return
#         ------
#         normalized tensor images of shape [B, C, H, W]
#         """
#         from skimage.color import rgb2hsv, hsv2rgb
#         from skimage.exposure import match_histograms

#         is_normalized: bool = False

#         reference_image_hsv: np.ndarray = rgb2hsv(reference_image)
#         reference_saturation: float = np.mean(reference_image_hsv[:, :, 1])

#         image_hsv: np.ndarray = rgb2hsv(image)
#         saturation: float = np.mean(image_hsv[:, :, 1])

#         if abs(saturation - reference_saturation) / reference_saturation > 0.75:
#             matched_hsv = match_histograms(image_hsv, reference_image_hsv, multichannel=True)
#             image_hsv[1] = matched_hsv[1]

#             image_out = (hsv2rgb(image_hsv) * 255).astype(np.uint8)
#             is_normalized = True
#             return image_out, is_normalized

#         return image, is_normalized


# @register_preprocessing(name="normalize_sharpness")
# class NormalizeSharpness(BasePreprocessing):
#     def __init__(self):
#         pass

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Normalize sharpness of a tensor image given a reference image.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         Return
#         ------
#         normalized tensor images of shape [B, C, H, W]
#         """
#         from skimage.filters import unsharp_mask

#         is_normalized: bool = False
#         reference_shaprness: float = calculate_sharpness_score(reference_image)
#         sharpness: float = calculate_sharpness_score(image)

#         if (sharpness - reference_shaprness) / reference_shaprness < 0.75:
#             is_normalized = True
#             image_out = (unsharp_mask(image) * 255).astype(np.uint8)
#             return image_out, is_normalized

#         return image, is_normalized


# @register_preprocessing(name="normalize_contrast")
# class NormalizeContrast(BasePreprocessing):
#     def __init__(self):
#         pass

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Normalize contrast of a tensor image given a reference image.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         Return
#         ------
#         normalized tensor images of shape [B, C, H, W]
#         """
#         from skimage.exposure import adjust_sigmoid

#         is_normalized: bool = False
#         reference_contrast: float = calculate_contrast_score(reference_image)
#         contrast: float = calculate_contrast_score(image)

#         if (contrast - reference_contrast) / contrast < 0.75:  # low contrast image
#             image_out = adjust_sigmoid(image)
#             is_normalized = True
#             return image_out, is_normalized

#         return image, is_normalized


# @register_preprocessing(name="equalize_histogram")
# class EqualizeHistogram(BasePreprocessing):
#     def __init__(self):
#         pass

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Normalize contrast of a tensor image given a reference image.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         Return
#         ------
#         normalized tensor images of shape [B, C, H, W]
#         """
#         from skimage.exposure import equalize_hist, is_low_contrast

#         is_normalized: bool = False
#         image_out: np.ndarray = image

#         if is_low_contrast(image):
#             H, W, C = image.shape
#             image_out = np.stack(
#                 [
#                     equalize_hist(image[:, :, channel])
#                     for channel in range(C)
#                 ],
#                 axis=-1
#             )
#             image_out = (image_out * 255).astype(np.uint8)
#             is_normalized = True

#         return image_out, is_normalized


# @register_preprocessing(name="high_resolution")
# class IncreaseResolution(BasePreprocessing):
#     def __init__(self):
#         self.scale_factor = 2.0

#     def process(self, image: np.ndarray, reference_image: np.ndarray, **kwargs) -> Tuple[np.ndarray, bool]:
#         """
#         Increase resolution of a tensor image given a reference image.

#         Parameters:
#         -----------
#         images:
#             Input tensor images of shape [B, C, H, W].

#         reference_images:
#             Tensor image used for referencing, shape [B, C, H, W]

#         Return
#         ------
#         normalized tensor images of shape [B, C, H, W]
#         """
#         is_normalized: bool = False
#         H, W, _ = image.shape

#         new_height = int(H * self.scale_factor)
#         new_width = int(W * self.scale_factor)
#         image_out: np.ndarray = resize_image(image, (new_height, new_width))

#         if image_out.shape != image.shape:
#             is_normalized = True

#         return image_out, is_normalized