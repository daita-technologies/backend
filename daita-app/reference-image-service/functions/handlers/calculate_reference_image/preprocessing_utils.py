import numpy as np
from typing import List, Union


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

def get_index_of_median_value(array: Union[List[float], np.ndarray]) -> int:
    """
    Find index of the median value in a list or 1-D arry
    """
    index: int = np.argsort(array)[len(array) // 2]
    return index