import os
import shutil
from pathlib import Path, PurePath
from typing import Tuple, List

import numpy as np
from numpy.typing import NDArray
from scipy.io import wavfile

from .validate import validate_path_exists


CWD = Path(os.getcwd())

def fp_to_abs(fp:Path|str) -> Path:
    """convert 'fp' to an absolute path"""
    fp = (
        Path(fp)
        if not (isinstance(fp, PurePath) or isinstance(fp, Path))
        else fp
    )
    if not fp.is_absolute():
        fp = CWD.joinpath(fp)
    fp.resolve()
    return fp


def fp_to_abs_validate(fp:Path|str) -> Path:
    fp = fp_to_abs(fp)
    validate_path_exists(fp)
    return fp


def check_exists(fp:Path|str, overwrite:bool) -> Tuple[Path, bool]:
    fp = fp_to_abs(fp)
    exists = fp.exists()
    if exists and not overwrite:
        raise FileExistsError(f"file or directory directory '{fp}' exists. set 'overwrite' to 'True' to overwrite its contents.")
    return fp, exists


def check_exists_file(fp:Path|str, overwrite:bool) -> Tuple[Path, bool]:
    """
    check that if a path exists, and, if it should be overwritten (`overwrite=True`),
    that the existing path points to a file, and not a directory
    """
    fp, exists = check_exists(fp, overwrite)
    if exists and overwrite and not fp.is_file():
        raise FileExistsError(f"path '{fp}' should not exist or be a file, but it is a directory")
    return fp, exists


def make_dir(dir_: str|Path, overwrite:bool) -> Path:
    dir_, exists = check_exists(dir_, overwrite)
    if not exists:
        dir_.mkdir()
    else:
        # if overwrite==False, 'check_exists' will have raised => no need for extra checks
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
