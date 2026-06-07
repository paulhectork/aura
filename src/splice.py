from typing import Literal, List, Tuple, Any
from pathlib import Path
import random

import numpy as np

from src.utils.validate import validate_type, validate_comparison, validate_isinlist, validate_float_isinrange, validate_pretty
from src.utils.io_op import check_exists_file
from src.utils.utils import frame_to_seconds, is_1darray, seconds_to_frame, to_mono, to_stereo, fade, is_1darray, apply_pan, apply_width, array_plot
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
    mode: int
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
        mode:int=2,
        pattern:str|None=None,
        repeat:float|None=10,
        overwrite:bool=False,
        crackle:bool=False
    ):
        # validate data
        overwrite = validate_pretty("overwrite", validate_type, i=overwrite, type_=bool)
        chunks = TrackList.read_from_dir(trackspath)
        outpath, exists = check_exists_file(outpath, overwrite)
        pattern_chunk = Track.read(pattern) if pattern is not None else None
        length = validate_pretty("length", validate_type, i=length, type_=float)
        nimpulses = validate_nimpulses_pretty(nimpulses)
        crackle = validate_pretty("crackle", validate_type, i=crackle, type_=bool)

        validate_pretty("mode", validate_type, i=mode, type_=int)
        validate_pretty("mode", validate_comparison, opname="gt", a=mode, b=0)
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

        # NOTE: all tracks are converted to mono: the mono chunks will be placed in stereo space
        #self.chunks = chunks.resample().to_mono()
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
        self.crackle = crackle
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
        if self.envelope == ENV_NONE:
            return chunk
        elif self.envelope == ENV_RANDOM:
            return Envelope.random().apply(chunk)
        elif isinstance(self.envelope, EnvelopeList):
            return self.envelope.get_one().apply(chunk)
        else:
            raise ValueError(f"error selecting envelope strategy. `Splice.envelope` should be `None`, `'random'` or `EnvelopeList`, but is: {type(self.envelope)}")

    def no_silence_once(self) -> np.ndarray:
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
        # mono => fill 1  channels with samples
        if self.nchannels == 1:
            data = self.no_silence_once()
        # stereo => fill `self.mode` channels with samples, then convert them back to stereo (2-channel track)
        else:
            # prepare individual tracks
            tracks = [
                self.no_silence_once()
                for _ in range(self.mode)
            ]
            # clip tracks to the shortest length
            min_len = min(t.shape[0] for t in tracks)
            tracks = [
                t[:min_len,] for t in tracks
            ]
            # combine in a single numpy array
            # `squeeze` is used if `self.mode==1`: np.stack() will then create a shape (nsamples,1),
            # and squeeze converts it back to (nsamples,): normal mono audio.
            data = np.stack([ t for t in tracks ], axis=1).squeeze()
            data = to_stereo(data)  # convert multichannel to stereo
            # apply widthapply_width
            data = apply_width(data, self.width, crackle=self.crackle)
        return data

    def impulses(self) -> np.ndarray:
        # calculate total number of impulses to generate for the whole output track duration.
        length_seconds = frame_to_seconds(self.length, self.rate)
        nimpulses = int((self.nimpulses / 60) * length_seconds)

        # define possible panning positions depending on `self.width` and `self.mode`.
        # pan_pos is an array of all possible panning positions, in -1..1 space.
        pan_positions = None
        if self.mode == 1:
            pan_positions = [0]
        else:
            pan_positions = np.linspace(-1*self.width, 1*self.width, self.mode)

        def pan_chunk(_chunk: np.ndarray):
            if self.nchannels != 1:
                return apply_pan(random.choice(pan_positions), _chunk)
            return _chunk

        def split_data(_data: np.ndarray, s: int, e:int) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
            # slicing changes depending on wether we're dealing with 1D or 2D arrays
            if is_1darray(_data):
                data_pre = _data[:s,]
                data_post = _data[e:,]
                data_overlap = _data[s:e,]
            else:
                data_pre = _data[:s,:]
                data_post = _data[e:,:]
                data_overlap = _data[s:e,:]
            return data_pre, data_overlap, data_post

        def place_chunk(_data:np.ndarray, _chunk:np.ndarray, pos: int):
            """
            shape _chunk: (samples,)
            shape _data: (samples, nchannels?)
            """
            if not is_1darray(_chunk):
                raise ValueError(f"in place_chunks, _chunk must be 1d array. got: {_chunk.shape}")

            dtype_orig = _chunk.dtype
            # find start and end positions in `_data`where chunk will be placed.
            s = pos
            e = pos+_chunk.shape[0]
            # clip `_chunk` so that it doesn't end after the track's length
            if e > self.length:
                e = self.length
                _chunk = _chunk[:e-s,]
            # split _data
            data_pre, data_overlap, data_post = split_data(data, s, e)
            # 2d array => stereo => pan the chunk
            if self.nchannels != 1:
                _chunk = pan_chunk(_chunk)
            # we are attempting to write in `data` at a position where there is aldready sound
            # => fade transition existing sound and new sound
            if np.count_nonzero(data_overlap) > 0:
                _chunk = fade(data_overlap, _chunk)

            # return the updated `data`.
            return np.concatenate([data_pre, _chunk, data_post], axis=0).astype(dtype_orig)

        # base empty ndarray
        if self.nchannels == 1:
            shape = (self.length)
        else:
            shape = (self.length, self.nchannels)
        data = np.array(np.zeros(shape))

        # fill
        n = 0  # tracks number of impulses used
        while n < nimpulses:
            pos = random.randint(0, data.shape[0])
            chunk = self.get_chunk_apply_env()
            data = place_chunk(data, chunk.data, pos)
            n += 1

        # use `apply_width`, not to actually change stereo width, but to add extra crackle.
        if self.crackle:
            if self.nchannels == 1:
                data = to_stereo(data)
                data = apply_width(data, self.width, self.crackle)
                data = to_mono(data)
            else:
                data = apply_width(data, self.width, self.crackle)

        return data


    def pipeline(self):
        if self.nimpulses == NO_SILENCE:
            data = self.no_silence()
        else:
            data = self.impulses()

        print("result:::", data, data.shape)
        array_plot(data, stack=False)
        track = Track(rate=self.rate, data=data, trackpath=self.outpath)
        track.write()
        return


