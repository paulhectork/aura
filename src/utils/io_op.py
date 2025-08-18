import os
import shutil
from pathlib import Path
from typing import Tuple, List

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


def write(fp:Path|str, rate:int, data:NDArray) -> None:
    return wavfile.write(fp, rate, data)

def read_from_dir(dp:str|Path) ->  List[Tuple[Tuple[int, NDArray], Path]]:
    """
    :returns: [ ((rate1, data1), fp1), ((rate2, data2), fp2), ... ]
    """
    dp = fp_to_abs(dp)
    if not dp.is_dir():
        raise ValueError(f"'dp' should be a path to an existing directory (dp=`{dp}`)")
    fp_list = [ fp.resolve() for fp in dp.iterdir() if fp.is_file() ]
    tracklist = []
    for fp in fp_list:
        try:
            tracklist.append(read(fp))
        except ValueError:
            print(f"skipping non-sound file '{fp}'")
    if not len(tracklist):
        raise ValueError(f"directory should contain at least one sound file (directory='{dp}', contents='{fp_list}')")

    return tracklist
