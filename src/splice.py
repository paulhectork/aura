from typing import Literal, List, Tuple, Any
from pathlib import Path

from src.utils.validate import validate_type, validate_comparison, validate_isinlist, validate_float_isinrange, validate_pretty
from src.utils.io_op import check_exists_file
from src.utils.utils import seconds_to_frame
from src.track import Track, TrackList
from src.envelope import Envelope, EnvelopeList

NO_SILENCE = "no-silence"
ENV_RANDOM = "random"
ENV_NONE = None

class Splice:

    chunks: TrackList
    outpath: Path
    length: int
    nimpulses: int|Literal["NO_SILENCE"]
    envelope: EnvelopeList|Literal["random"]|None
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
        envelope:str|None=ENV_NONE,
        nchannels:Literal[1,2]=2,
        width:float=1,
        mode:Literal[2,3,"range"]=2,
        pattern:str|None=None,
        repeat:float|None=10,
        overwrite:bool=False
    ):
        # validate data
        overwrite = validate_pretty("overwrite", validate_type, i=overwrite, type_=bool)
        chunks = TrackList.read_from_dir(trackspath)
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

        if envelope != ENV_RANDOM and envelope != ENV_NONE:
            try:
                envelope_data = EnvelopeList.read(envelope)  # pyright: ignore
            except Exception as e:
                raise e
                print(f"could not read envelopes from file: {envelope}. File should contain the output of Envelope.to_dict()")
                exit(1)
        else:
            envelope_data = envelope

        # NOTE: all tracks are converted to mono: the mono chunks will be placed in stereo space
        self.chunks = chunks.resample().to_mono()
        self.outpath = outpath
        self.length = seconds_to_frame(length, chunks.rate)
        self.nimpulses = nimpulses
        self.envelope = envelope_data  # pyright: ignore
        self.nchannels = nchannels
        self.width = width
        self.mode = mode
        self.pattern = pattern_chunk
        self.pattern_repeat = seconds_to_frame(repeat, chunks.rate)  # pyright:ignore
        self.overwrite = overwrite
        self.rate = chunks.rate
        return

    def get_chunk_apply_env(self) -> Track:
        """
        1. select a chunk and apply an env to it
        NOTE: chunks and envs are selected and applied at random.
        """
        chunk = self.chunks.get_one()
        if self.envelope == ENV_NONE:
            return chunk
        elif self.envelope == ENV_RANDOM:
            return Envelope.random().apply(chunk)
        elif isinstance(self.envelope, EnvelopeList):
            return self.envelope.get_one().apply(chunk)
        else:
            raise ValueError(f"error selecting envelope strategy. `Splice.envelope` should be `None`, `'random'` or `EnvelopeList`, but is: {type(self.envelope)}")

    def pipeline(self):
        # NOTE: envs successfully applied !
        # TODO: position chunks in space !
        for _ in self.chunks.tracklist:
            self.get_chunk_apply_env()


