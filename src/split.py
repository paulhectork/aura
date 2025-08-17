from typing import Literal

from track import Track
from utils.io_op import read, fp_to_abs
from utils.utils import seconds_to_frame
from utils.validate import validate_isint, validate_isfloat, validate_isinlist

class Split:
    def __init__(
        self,
        trackname:str,
        output:str,
        length: float,
        dev: float | None = 0,
        numchunks: int | None = 0,
        mode: Literal["stereo", "mono"] | None = None
    ):
        # validate data
        track = Track(read(trackname))
        output = fp_to_abs(output)

        validate_isfloat(length)
        if numchunks is not None:
            validate_isint(numchunks)
        if dev is not None:
            validate_isfloat(dev)
        if mode is not None:
            validate_isinlist(mode, ["stereo", "mono"])

        # define defaults and do conversions
        length = seconds_to_frame(length, track.samplerate)
        if dev is None:
            dev == 0
        if numchunks is None or numchunks == 0:
            numchunks = track.nframes / length  # track length / splitted chunk length
        if mode is None:
            mode = "mono" if track.nchannels == 1 else "stereo"  # define default based on number of channels in input tracks
        if mode == "mono":
            track = track.to_mono()

        self.track = track
        self.output = output
        self.l = length  # internally stored at self.track's sampling rate
        self.n = numchunks
        self.dev = dev
        self.mode = mode

