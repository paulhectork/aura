from typing import Literal, List
from pathlib import Path
import re

import numpy as np
from numpy.typing import NDArray
from scipy.stats import truncnorm

from track import Track
from utils.io_op import make_dir
from utils.utils import seconds_to_frame, get_chunk_ends
from utils.validate import validate_isint, validate_isfloat, validate_isinlist, validate_islt

class Split:

    track: Track
    outpath: Path
    length: int
    nchunks: int
    dev: float
    nchannels: Literal[1,2]
    split_all: bool
    chunk_pos: NDArray
    chunks: List[Track]

    def __init__(
        self,
        trackpath:str,
        outpath:str,
        length: float,
        dev: float | None = 0,
        nchunks: int | None = 0,
        nchannels: Literal[1,2] | None = None,
        overwrite: bool = False
    ):
        # validate data
        track = Track.read(trackpath)
        outpath = make_dir(outpath, overwrite)  # pyright: ignore

        validate_isfloat(length)
        if nchunks is not None:
            validate_isint(nchunks)
        if dev is not None:
            validate_isfloat(dev)
            validate_islt(dev, length)
        if nchannels is not None:
            validate_isint(nchannels)
            nchannels = int(nchannels)  # pyright: ignore
            validate_isinlist(nchannels, [1, 2])

        # define defaults and do conversions
        length = seconds_to_frame(length, track.samplerate)
        dev = 0 if dev is None else float(dev)
        dev = seconds_to_frame(dev, track.samplerate)
        if nchunks is None or nchunks == 0:
            nchunks = int(track.nframes / length)  # track length / splitted chunk length
        if nchannels is None:
            nchannels = 1 if track.nchannels == 1 else 2  # define default based on number of channels in input track
        if nchannels == 1:
            track = track.to_mono()
        else:
            track = track.to_stereo()
        # flag to split the entire track into consecutive chunks of lenght `length` if `nchunks * length` == `track.nframes`
        split_all = nchunks * length == track.nframes  # pyright:ignore .

        self.track = track
        self.outpath = outpath  # pyright: ignore
        self.length = length  # internally stored at self.track's sampling rate
        self.nchunks = nchunks  # pyright: ignore
        self.dev = dev
        self.nchannels = nchannels
        self.split_all = split_all

    def pipeline(self):
        """
        split track into chunks
        """
        self.make_chunk_pos().make_chunks().write_chunks()
        return self

    def to_outpath(self, n:int) -> Path:
        """
        generate an outpath track name for a chunk
        :param n: the position of this chunk in the `self.chunk` array
        """
        basename_in = re.sub(r"\.[^\.]+$", "", self.track.trackpath.name)  # pyright: ignore . file name without path and extension
        return self.outpath.joinpath(f"{basename_in}_chunk{n}.wav")

    def make_chunk_pos(self):
        """
        generate chunk positions for `self.track`
        chunk positions are an NDArray of shape `(n,2)`: storing the start and end frame of each chunk.
        [ [start1,end1], [start2,end2], ... ]

        done by calculating 3 ndarrays:
        - chunk_lenghts : lenghts of all chunks (with standard deviation)
        - chunk_starts  : start position of all chunks
        - chunk_ends    : end position of all chunks
        """
        # 1; calculate chunk lengths, applying standard deviation if needed
        #
        #  chunk lengths (in number of frames) are calculated using a truncated standard deviation. truncation allows to set min/max values for the standard deviations.
        # we truncate to (0, 2*length)
        # `truncnorm.rvs` expects min/max to be expressed in `number of standard deviations` => we convert from absoute min/max values to numbe of standard deviations
        abs_to_std = lambda x: (x - self.length) / self.dev

        if self.dev > 0:
            min_ = abs_to_std(0)
            max_ = abs_to_std(2*self.length)

            chunk_lengths = np.array(truncnorm.rvs(
                min_, max_,
                loc=self.length,
                scale=self.dev,
                size=self.nchunks
            ))
            assert chunk_lengths[chunk_lengths < 0].shape[0] == 0
            assert chunk_lengths[chunk_lengths > 2*self.length].shape[0] == 0
        else:
            chunk_lengths = np.array([self.length for _ in range(self.nchunks)])

        # 2: calculate chunk starting positions
        # if split_all, all chunks are successive. otherwise, chunks are positionned at random
        if self.split_all:
            # cumsum = cumulative sum: each new item is the sum of all preceding items
            # we add an item at pos 0: the starting point of the 1st chunk.
            chunk_starts = np.cumsum(np.concat([[0], chunk_lengths]))
            chunk_ends = chunk_starts[1:]
            max_chunk_end = chunk_ends[-1]  # last item is the end point of the last chunk
            chunk_starts = chunk_starts[:-1]  # remove the last item, since `chunk_starts` only keeps starting positions
        else:
            chunk_starts = np.random.default_rng().integers(0, self.track.nframes, self.nchunks)
            chunk_ends = get_chunk_ends(chunk_starts, chunk_lengths)  # pyright: ignore
            max_chunk_end = np.max(chunk_ends)

        # resize `chunk_*` if the last chunk end is higher than the track length (possible because of standard deviation)
        if max_chunk_end > self.track.nframes - 1:
            r = (self.track.nframes - 1) / max_chunk_end
            chunk_starts = np.rint(chunk_starts * r)  # rint = round to int
            chunk_lengths = np.rint(chunk_lengths * r)
            chunk_ends = get_chunk_ends(chunk_starts, chunk_lengths)
            assert np.max(chunk_ends) <= self.track.nframes, f"last chunk ends after track end. max chunk end: {np.max(chunk_ends)}, track length: {self.track.nframes}"

        # 3: extract the chunk positions
        # [ [start1,end1], [start2,end2], ... ]
        self.chunk_pos = np.transpose(np.vstack([chunk_starts, chunk_ends])).astype(int)
        return self


    def make_chunks(self):
        """
        use self.chunk_pos as indices and populate `self.chunks`
        """
        self.chunks = []
        for i, (start, end) in enumerate(self.chunk_pos):
            chunk = self.track.data[start:end]
            # asert `chunk` has the same number of dimensions and same number of channels as `self.track`
            assert_nchannels = chunk.shape[1] == self.track.data.shape[1] \
                if len(self.track.data.shape) > 1 \
                else True  # if mono, then `len(track.shape)` = 1
            assert len(chunk.shape) == len(self.track.data.shape) \
                and assert_nchannels

            self.chunks.append(Track(
                samplerate=self.track.samplerate,
                data=chunk,
                trackpath=self.to_outpath(i)
            ))

        return self

    def write_chunks(self):
        """
        write self.chunks to outpath folder
        """
        for chunk in self.chunks:
            chunk.write()