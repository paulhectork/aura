import os
import shutil
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
        fp = CWD.joinpath(fp)
    fp.resolve()
    return fp


def fp_to_abs_validate(fp:Path|str) -> Path:
    fp = fp_to_abs(fp)
    validate_path_exists(fp)
    return fp


def make_dir(dir_: str|Path, overwrite:bool) -> Path:
    dir_ = fp_to_abs(dir_)
    exists = dir_.exists()
    if not exists:
        dir_.mkdir()
    else:
        if not overwrite:
            raise FileExistsError(f"directory '{dir_}' exists. use '--overwrite' to overwrite its contents.")
        else:
            # empty directory contents qnd recreate it
            shutil.rmtree(dir_)
            dir_.mkdir()
    return dir_


def read(fp:Path|str) -> Tuple[Tuple[int, NDArray], Path]:
    fp = fp_to_abs_validate(fp)
    return wavfile.read(fp), fp


def write(fp:Path|str, samplerate:int, data:NDArray) -> None:
    return wavfile.write(fp, samplerate, data)

