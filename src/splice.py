from typing import Literal, List, Tuple, Any
from pathlib import Path

from utils.validate import validate_type, validate_comparison, validate_isinlist, validate_float_isinrange
from utils.io_op import check_exists_file
from utils.utils import seconds_to_frame
from utils.constants import NO_SILENCE
from track import Track

class Splice:

    chunks: List[Track]
    outpath: Path
    length: int
    nimpulses: int|"NO_SILENCE"
    envelope: Any
    nchannels: int
    width: float
    mode: int|Literal["range"]
    pattern: Path
    patter_repeat: int
    overwrite: bool
    rate: int

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
            validate_comparison("eq", nimpulses, NO_SILENCE)
        validate_isinlist(nchannels, [1,2])
        validate_float_isinrange(width, 0, 1, inclusive=True)
        validate_isinlist(mode, [2,3,"range"])  #NOTE mode has no effect if 'nchannels' != 2

        if nchannels == 1:
            width = 0.

        if repeat is not None:
            repeat = validate_type(repeat, float)

        ##########################################################
        #TODO `envelope`
        #TODO extract highest rate from `chunks` and normalize all chunks to the same rate
        ##########################################################

        self.chunks = chunks
        self.outpath = outpath
        self.length = seconds_to_frame(length, )
        self.nimpulses = self.nimpulses
        self.envelope = envelope
        self.nchannels = nchannels
        self.width = width
        self.mode = mode
        self.pattern = pattern
        self.patter_repeat = repeat
        self.overwrite = overwrite



