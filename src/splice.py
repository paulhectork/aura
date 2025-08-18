from typing import Literal
from pathlib import Path

from utils.validate import validate_type, validate_iseq, validate_isinlist, validate_float_isinrange
from utils.io_op import check_exists_file
from utils.constants import NO_SILENCE
from track import Track

class Splice:
    def __init__(
        self,
        trackspath:str|Path,
        outpath:str|Path,
        length:float,
        nimpulses:int|str=NO_SILENCE,
        envelope:str="random",
        nchannels:Literal[1,2]=2,
        width:float=1,
        mode:Literal[2,3,"range"]=2,
        pattern:str|None=None,
        repeat:int|None=None,
        overwrite:bool=False
    ):
        # validate data
        overwrite = validate_type(overwrite, bool)
        chunks = Track.read_from_dir(trackspath)
        outpath, exists = check_exists_file(outpath, overwrite)
        if pattern is not None:
            pattern = Track.read(pattern)  # pyright: ignore

        length = validate_type(length, float)
        try:
            nimpulses = validate_type(nimpulses, int)
        except ValueError:
            validate_iseq(nimpulses, NO_SILENCE)
        validate_isinlist(nchannels, [1,2])
        validate_float_isinrange(width, 0, 1, inclusive=True)
        validate_isinlist(mode, [2,3,"range"])  #NOTE mode has no effect if 'nchannels' != 2

        if repeat is not None:
            repeat = validate_type(repeat, float)

        #TODO `envelope`



