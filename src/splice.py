from typing import Literal, List, Tuple, Any
from pathlib import Path
import textwrap
import random

import numpy as np
from tqdm import tqdm

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
    nlines: int
    pattern: Track|None
    pattern_repeat: int
    overwrite: bool
    rate: int
    crackle: bool
    visualize: bool

    def __init__(
        self,
        trackspath:str|Path,
        outpath:str|Path,
        length:float,
        nimpulses:int|Literal["no-silence"]=NO_SILENCE,  # pyright:ignore
        envelope:str|None=ENV_NONE,
        nchannels:Literal[1,2]=2,
        width:float=1,
        nlines:int=2,
        pattern:str|None=None,
        repeat:float|None=10,
        overwrite:bool=False,
        crackle:bool=False,
        visualize: bool=False
    ):
        # validate data
        overwrite = validate_pretty("overwrite", validate_type, i=overwrite, type_=bool)
        chunks = TrackList.read_from_dir(trackspath)
        outpath, exists = check_exists_file(outpath, overwrite)
        pattern_chunk = Track.read(pattern) if pattern is not None else None
        nimpulses = validate_nimpulses_pretty(nimpulses)
        crackle = validate_pretty("crackle", validate_type, i=crackle, type_=bool)
        visualize = validate_pretty("visualize", validate_type, i=visualize, type_=bool)
        length = validate_pretty("length", validate_type, i=length, type_=float)

        validate_pretty("nlines", validate_type, i=nlines, type_=int)
        validate_pretty("nlines", validate_comparison, opname="gt", a=nlines, b=0)
        validate_pretty("nchannels", validate_isinlist, i=nchannels, vallist=[1,2])
        validate_pretty("width", validate_float_isinrange, i=width, min_=0, max_=1, inclusive=True)

        if repeat is not None:
            repeat = validate_pretty("repeat", validate_type, i=repeat, type_=float)
        elif pattern is not None:
            repeat = 10.0

        envelope_raw = envelope
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
        # if the track is in mono, set `nlines` to 1 so we only work on 1 channel
        # effectively, this disables nlines if 'nchannels' != 2
        if nchannels != 2:
            nlines = 1

        length_seconds = length
        length = seconds_to_frame(length, chunks.rate)

        # NOTE: all tracks are converted to mono: the mono chunks will be placed in stereo space
        self.length_seconds = length_seconds
        self.length = length
        self.chunks = chunks.resample().to_mono()
        self.outpath = outpath
        self.nimpulses = nimpulses
        self.envelope = envelope_data  # pyright: ignore
        self.nchannels = nchannels
        self.width = width
        self.nlines = nlines
        self.pattern = pattern_chunk
        self.pattern_repeat = seconds_to_frame(repeat, chunks.rate)  # pyright:ignore
        self.overwrite = overwrite
        self.rate = chunks.rate
        self.crackle = crackle
        self.visualize = visualize

        # prgress bar. see self.pb property
        self._pb = None

        print(textwrap.dedent(f"""
            aura::splice - fill a track with randomly positionned chunks
                * input:
                    * path to chunks.... {trackspath}
                    * number of chunks.. {len(self.chunks.tracklist)}
                * output:
                    * path.............. {self.outpath}
                    * length (s.) ...... {self.length_seconds}
                    * impulses/minute... {self.nimpulses}
                    * nlines............ {self.nlines}
                    * width............. {self.width}
                    * channels.......... {self.nchannels}
                    * envelope.......... {envelope}
        """))
        return

    @property
    def pb(self):
        if not self._pb:
            # define a progress bar
            # we define the pbar as a class object so that several functions can update it at once.
            if self.nimpulses == NO_SILENCE:
                desc = f"splicing (length: {self.length_seconds}s., no silence)"
                total = self.length * self.nlines
            else:
                desc=f"splicing chunks (length={self.length_seconds}s., {self.nimpulses} impulses/s.)"
                total = int(self.nimpulses * self.length_seconds / 60)
            self._pb = tqdm(desc=desc, total=total)  # pyright: ignore
        return self._pb

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
        # output ndarray
        data = np.zeros(self.length, dtype=np.float64)
        # track total # of inserted frames.
        i = 0
        # for output dtype conversion
        dtype_orig = None
        while i < self.length:
            # 1darray
            chunk = self.get_chunk_apply_env().data
            # data's final dtyle
            if dtype_orig is None:
                dtype_orig = chunk.dtype
            # if necessary, clip chunk so that data is not larger than self.length.
            nframes = chunk.shape[0]
            if i + nframes > self.length:
                nframes = self.length - i
                chunk = data[:nframes]
            # add the chunk to `data`
            data[i:i+nframes] = chunk
            i += nframes
            self.pb.update(nframes)
        data = data.astype(dtype_orig)
        return data

    def no_silence(self) -> np.ndarray:
        """
        fill strategy if `nimpulses` is "no-silence".
        fill `self.nlines` tracks (1 or more) with chunks until track duration is completed.
        then, merge these tracks in stereo space.
        """
        # mono => fill 1  channels with samples
        if self.nchannels == 1:
            data = self.no_silence_once()
        # stereo => fill `self.nlines` channels with samples, then convert them back to stereo (2-channel track)
        else:
            # prepare individual tracks and  combine in a single numpy array
            # `squeeze` is used if `self.nlines==1`: np.stack() will then create a shape (nsamples,1),
            # and squeeze converts it back to (nsamples,): normal mono audio.
            # shape: (samples, nchannels?)
            data = np.stack(
                [ self.no_silence_once() for _ in range(self.nlines) ],
                axis=1
            ).squeeze()
            # convert multichannel to stereo
            data = to_stereo(data)
            # apply widthapply_width
            data = apply_width(data, self.width, crackle=self.crackle)
        return data

    def impulses(self) -> np.ndarray:
        """
        fill strategy if `nimpulses` is a number (# of impulses per minute).
        fill the track with `nimpulses` chunks per minute placed randomly in time and panned randomly in stereo space.
        """
        length_seconds = frame_to_seconds(self.length, self.rate)
        nimpulses = int(self.nimpulses * length_seconds / 60)

        # define possible panning positions depending on `self.width` and `self.nlines`.
        if self.nlines == 1:
            pan_positions = [0]
        else:
            pan_positions = np.linspace(-self.width, self.width, self.nlines)
        # pre-generate an array containing panning positions for all chunks
        if self.nchannels != 1:
            pan_choices = np.random.choice(len(pan_positions), size=nimpulses)
        # pre-generate an array with all starting positions for all chunks
        positions = np.random.randint(0, self.length, size=nimpulses)

        # output datatype for the full track
        dtype_orig = self.get_chunk_apply_env().data.dtype
        # datatype for calculations and processing: dtype_orig should be in int16,
        # which is quickly overflown when doing calculations, which will cause distorsion
        # => for all calculations, use `float32`. at the end, convert back to `dtype_orig`
        # to avoid distorsion when saving to output file
        dtype_calc = np.float64

        # create output ndarray
        if self.nchannels == 1:
            data = np.zeros(self.length, dtype=dtype_calc)
        else:
            data = np.zeros((self.length, self.nchannels), dtype=dtype_calc)

        # place the chunks
        for i in range(nimpulses):
            start = positions[i]
            # always a 1-d array: chunks are converted to mono in __init__
            chunk = self.get_chunk_apply_env().data.astype(dtype_calc)
            # clip chunk to track boundary
            end = min(start + chunk.shape[0], self.length)
            chunk = chunk[:end - start]
            # pan: apply before writing (stereo only)
            if self.nchannels != 1:
                chunk = apply_pan(pan_positions[pan_choices[i]], chunk)  # pyright: ignore
            # overlap: there is alsready sound where chunk should be placed => fade chunk with existing sound.
            overlap = data[start:end] if self.nchannels == 1 else data[start:end, :]
            if np.any(overlap != 0):
                chunk = fade(overlap, chunk)
            # write to the output ndarray
            if self.nchannels == 1:
                data[start:end] = chunk
            else:
                data[start:end, :] = chunk
            self.pb.update(1)

        # convert output array to original chunk dtype to avoid distorision
        data = data.astype(dtype_orig)

        # optional crackle via apply_width
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
        self.pb.close()

        if self.visualize:
            array_plot(data, stack=False)
        track = Track(rate=self.rate, data=data, trackpath=self.outpath)
        track.write()
        print()
        print(f"aura::splice: output track saved to: {self.outpath}")
        return


