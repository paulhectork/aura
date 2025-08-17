import os

import numpy as np
from scipy.io import wavfile

from .constants import CWD
from .validate import validate_path_exists


def fp_to_abs(fp:os.PathLike) -> os.PathLike:
    """convert 'fp' to an absolute path"""
    if not os.path.isabs(fp):
        fp = os.path.abspath(os.path.join(CWD, fp))
    return fp


def fp_to_abs_validate(fp:os.PathLike) -> os.PathLike:
    fp = fp_to_abs(fp)
    validate_path_exists(fp)
    return fp


def read(fp:os.PathLike) -> np.array:
    fp = fp_to_abs_validate(fp)
    return wavfile.read(fp)


def write(fp:os.PathLike, data:np.ndarray) -> None:
    # other params tbd
    raise NotImplementedError

