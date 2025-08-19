from typing import Literal, List, Tuple, Any
from pathlib import Path

from utils.validate import validate_type, validate_comparison, validate_isinlist, validate_float_isinrange
from utils.io_op import check_exists_file
from utils.utils import seconds_to_frame
from utils.constants import NO_SILENCE
from track import Track, TrackList

class Splice:

    chunks: TrackList
    outpath: Path
    length: int
    nimpulses: int|Literal["NO_SILENCE"]
    envelope: Any
    nchannels: int
    width: float
    mode: int|Literal["range"]
    pattern: Track
    patter_repeat: int
    overwrite: bool
    rate: int

    def __init__(
        self,
        trackspath:str|Path,
        outpath:str|Path,
        length:float,
        nimpulses:int|Literal["NO_SILENCE"]=NO_SILENCE,  # pyright:ignore
        envelope:str="random",
        nchannels:Literal[1,2]=2,
        width:float=1,
        mode:Literal[2,3,"range"]=2,
        pattern:str|None=None,
        repeat:float|None=10,
        overwrite:bool=False
    ):
        # validate data
        overwrite = validate_type(overwrite, bool)
        chunks = TrackList.read_from_dir(trackspath).to_mono()  # all tracks are converted to mono: the mono chunks will be placed in stereo space
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
        elif pattern is not None:
            repeat = float(10)

        ##########################################################
        #TODO `envelope`
        #TODO extract highest rate from `chunks` and normalize all chunks to the same rate
        ##########################################################

        self.chunks = chunks
        self.outpath = outpath
        self.length = seconds_to_frame(length, chunks.rate)
        self.nimpulses = nimpulses
        self.envelope = envelope
        self.nchannels = nchannels
        self.width = width
        self.mode = mode
        self.pattern = pattern
        self.pattern_repeat = seconds_to_frame(repeat, chunks.rate)  # pyright:ignore
        self.overwrite = overwrite
        self.rate = chunks.rate



