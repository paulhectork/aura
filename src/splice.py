from pathlib import Path

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
        nchannels:int=2,
        width:float=1,
        mode:int=2,
        pattern:str|None=None,
        repeat:int|None=None,
    ):
        chunks = Track.read_from_dir(trackspath)
        pass
