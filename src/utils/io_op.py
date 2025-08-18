import os
from pathlib import Path
from typing import Tuple

import numpy as np
from numpy.typing import NDArray
from scipy.io import wavfile

from .validate import validate_path_exists


CWD = Path(os.getcwd())

def fp_to_abs(fp:Path|str) -> Path:
    """convert 'fp' to an absolute path"""
    fp = Path(fp)
    if not fp.is_absolute():
        fp = CWD.joinpath(fp).resolve()
    return fp


def fp_to_abs_validate(fp:Path|str) -> Path:
    fp = fp_to_abs(fp)
    validate_path_exists(fp)
    return fp


def read(fp:Path|str) -> Tuple[int, NDArray]:
    fp = fp_to_abs_validate(fp)
    return wavfile.read(fp)


def write(fp:Path|str, data:NDArray) -> None:
    # other params tbd
    raise NotImplementedError

