from typing import Literal, List, Tuple, Any
from pathlib import Path

from src.utils.validate import validate_type, validate_comparison, validate_isinlist, validate_float_isinrange, validate_pretty
from src.utils.io_op import check_exists_file
from src.utils.utils import seconds_to_frame
from src.utils.constants import NO_SILENCE
from src.track import Track, TrackList
from src.envelope import Envelope, EnvelopeList

class Splice:

    chunks: TrackList
    outpath: Path
    length: int
    nimpulses: int|Literal["NO_SILENCE"]
    envelope: Any
    nchannels: int
    width: float
    mode: int|Literal["range"]
    pattern: Track|None
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
        overwrite = validate_pretty("overwrite", validate_type, i=overwrite, type_=bool)
        chunks = TrackList.read_from_dir(trackspath).to_mono()  # all tracks are converted to mono: the mono chunks will be placed in stereo space
        outpath, exists = check_exists_file(outpath, overwrite)
        pattern_chunk = Track.read(pattern) if pattern is not None else None
        length = validate_pretty("length", validate_type, i=length, type_=float)
        try:
            nimpulses = validate_pretty("nimpulses", validate_type, i=nimpulses, type_=int)
        except ValueError:
            validate_pretty("nimpulses", validate_comparison, "eq", a=nimpulses, b=NO_SILENCE)
        #NOTE mode has no effect if 'nchannels' != 2
        validate_pretty("mode", validate_isinlist, i=mode, vallist=[2,3,"range"])
        validate_pretty("nchannels", validate_isinlist, i=nchannels, vallist=[1,2])
        validate_pretty("width", validate_float_isinrange, i=width, min_=0, max_=1, inclusive=True)

        if nchannels == 1:
            width = 0.

        if repeat is not None:
            repeat = validate_pretty("repeat", validate_type, i=repeat, type_=float)
        elif pattern is not None:
            repeat = 10.0

        ##########################################################
        #TODO `envelope`
        #TODO extract highest rate from `chunks` and normalize all chunks to the same rate
        ##########################################################

        self.chunks = chunks.resample()
        self.outpath = outpath
        self.length = seconds_to_frame(length, chunks.rate)
        self.nimpulses = nimpulses
        self.envelope = envelope
        self.nchannels = nchannels
        self.width = width
        self.mode = mode
        self.pattern = pattern_chunk
        self.pattern_repeat = seconds_to_frame(repeat, chunks.rate)  # pyright:ignore
        self.overwrite = overwrite
        self.rate = chunks.rate

        # print(EnvelopeList.random().to_list())



