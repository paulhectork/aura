from typing import Literal, List, Tuple, Any
from pathlib import Path

import numpy as np

from src.utils.validate import validate_type, validate_comparison, validate_isinlist, validate_float_isinrange, validate_pretty
from src.utils.io_op import check_exists_file
from src.utils.utils import seconds_to_frame
from src.track import Track, TrackList
from src.envelope import Envelope, EnvelopeList

NO_SILENCE = "no-silence"
ENV_RANDOM = "random"
ENV_NONE = None

def validate_nimpulses(nimpulses: int|str) -> int|Literal["no-silence"]:
    # nimpulses must be int or "no-silence"
    try:
        return validate_type(nimpulses, int)
    except ValueError:
        validate_comparison("eq", a=nimpulses, b=NO_SILENCE)
        return nimpulses  # pyright: ignore


def validate_nimpulses_pretty(nimpulses: int|str) -> int|Literal["no-silence"]:
    return validate_pretty("nimpulses", validate_nimpulses, nimpulses=nimpulses)


class Splice:

    chunks: TrackList
    outpath: Path
    length: int
    nimpulses: int|Literal["no-silence"]
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
        nimpulses:int|Literal["no-silence"]=NO_SILENCE,  # pyright:ignore
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
        nimpulses = validate_nimpulses_pretty(nimpulses)

        validate_pretty("mode", validate_isinlist, i=mode, vallist=[2,3,"range"])
        validate_pretty("nchannels", validate_isinlist, i=nchannels, vallist=[1,2])
        validate_pretty("width", validate_float_isinrange, i=width, min_=0, max_=1, inclusive=True)

        if repeat is not None:
            repeat = validate_pretty("repeat", validate_type, i=repeat, type_=float)
        elif pattern is not None:
            repeat = 10.0

        if envelope != ENV_RANDOM and envelope != ENV_NONE:
            try:
                envelope_data = EnvelopeList.read(envelope)  # pyright: ignore
            except Exception as e:
                print(f"could not read envelopes from file: {envelope}. File should contain the output of Envelope.to_dict()")
                exit(1)
        else:
            envelope_data = envelope

        # set contextual defaults and force conditionnal values for some options depending on other options.
        # disable width on stereo
        if nchannels == 1:
            width = 0.
        # if the track is in mono, set `mode` to 1 so we only work on 1 channel
        # effectively, this disables mode if 'nchannels' != 2
        if nchannels != 2:
            mode = 1
        # "range" cannot be usd in NO_SILENCE mode
        if mode == "range" and nimpulses == NO_SILENCE:
            mode = 3

        # NOTE: all tracks are converted to mono: the mono chunks will be placed in stereo space
        # TODO fix distorsion generated here
        c = chunks.tracklist[0]
        print("PRE MODIF", c.data.shape, c.data.min(), c.data.max())
        #self.chunks = chunks.resample().to_mono()
        self.chunks = chunks.resample().to_mono()
        print("POST MODIF", c.data.shape, c.data.min(), c.data.max())
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
        chunks and envs are selected and applied at random.
        """
        # NOTE: necessary to return a copy of the track. otherwise,
        # inplace mutation of track.data happens when applying an env:
        # each time envelope.apply(track) is called, the track is modified
        # with the env => track volume will quickly tend to 0.
        chunk = self.chunks.get_one(copy_track=True)
        print("MINIMUM VALUE IN CHUNK", chunk.data.min(0))
        print("MAXIMUM VALUE IN CHUNK", chunk.data.max(0))

        if self.envelope == ENV_NONE:
            return chunk
        elif self.envelope == ENV_RANDOM:
            return Envelope.random().apply(chunk)
        elif isinstance(self.envelope, EnvelopeList):
            return self.envelope.get_one().apply(chunk)
        else:
            raise ValueError(f"error selecting envelope strategy. `Splice.envelope` should be `None`, `'random'` or `EnvelopeList`, but is: {type(self.envelope)}")

    def fill_no_silence(self) -> np.ndarray:
        """
        fill 1 track with chunks until self.length has been reached
        """
        data = self.get_chunk_apply_env().data
        l = data.shape[0]
        while l < self.length:
            chunk = self.get_chunk_apply_env().data
            data = np.concatenate([data, chunk], axis=0)
            l = data.shape[0]
        return data

    def no_silence(self) -> np.ndarray:
        if self.nchannels == 1:
            data = self.fill_no_silence()
            print("OKI !!!")
        elif self.nchannels == 2:
            if self.mode == "range":
                print("unsupported option combination !!!")
                raise
            # self.mode == 2 or 3.
            else:
                # prepare individual tracks
                tracks = [
                    self.fill_no_silence()
                    for _ in range(self.mode)
                ]
                # clip tracks to the shortest length
                min_len = min(t.shape[0] for t in tracks)
                tracks = [
                    t[:min_len,] for t in tracks
                ]
                # combine in a single numpy array
                data = np.stack([ t for t in tracks ], axis=1)
                # convert 3 channels back to stereo by distributing the center channel along L and R channels
                if self.mode == 3:
                    track_center = data[:,1] / 2
                    tracks_lr = np.stack([ data[:,0], data[:,2] ], axis=1)
                    # add center to L and R + multiply by 2/3 to renormalize volume.
                    data = np.apply_along_axis(
                        lambda x: (x + track_center) * (2/3),
                        axis=0,
                        arr=tracks_lr
                    )
                # TODO apply width
        else:
            print("unsupported option combination !!!")
            raise
        print("MINIMUM VALUE IN TRACK", data.min(0))
        print("MAXIMUM VALUE IN TRACK", data.max(0))
        return data


    def pipeline(self):
        # NOTE: envs successfully applied !
        # TODO: position chunks in space !
        from src.utils.utils import array_plot
        if self.nimpulses == NO_SILENCE:
            data = self.no_silence()
            print("result:::", data, data.shape)
            array_plot(data, stack=False)

            track = Track(rate=self.rate, data=data, trackpath=self.outpath)
            track.write()


