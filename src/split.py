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
        nchunks: int | None = 0,
        nchannels: Literal[1,2] | None = None
    ):
        # validate data
        track = Track(read(trackname))
        output = fp_to_abs(output)

        validate_isfloat(length)
        if nchunks is not None:
            validate_isint(nchunks)
        if dev is not None:
            validate_isfloat(dev)
        if nchannels is not None:
            validate_isint(nchannels)
            nchannels = int(nchannels)
            validate_isinlist(nchannels, [1, 2])

        # define defaults and do conversions
        length = seconds_to_frame(length, track.samplerate)
        if dev is None:
            dev == 0
        if nchunks is None or nchunks == 0:
            nchunks = track.nframes / length  # track length / splitted chunk length
        if nchannels is None:
            nchannels = 1 if track.nchannels == 1 else 2  # define default based on number of channels in input track
        if nchannels == 1:
            track = track.to_mono()
        else:
            track = track.to_stereo()

        self.track = track
        self.output = output
        self.l = length  # internally stored at self.track's sampling rate
        self.n = nchunks
        self.dev = dev
        self.nchannels = nchannels

