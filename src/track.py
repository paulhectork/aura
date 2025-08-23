from typing import Tuple, List
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from scipy.signal import resample

from utils.io_op import read, write, read_from_dir
from utils.utils import frame_to_seconds, seconds_to_frame


def get_nchannels(data:NDArray) -> int:
        if len(data.shape) == 1:
            return 1
        elif len(data.shape) == 2:
            return data.shape[1]
        else:
            raise ValueError(f"unexpected shape of data: expected (x,) or (x,y), got {data.shape}")


class Track:
    def __init__(self, rate: int, data: NDArray, trackpath:Path|None = None):
        """
        :param rate: the sampling rate of the track
        :param data: 1 or 2d NDArray containing the track
        :param trackpath: path to the track file (optional; a trackpath that does not exist on the filesystem may be provided, for example to use `Track` as an interface to write a new track to file)
        """
        self.nchannels = get_nchannels(data)
        self.rate = rate
        self.nframes = data.shape[0]  # number of frames in Track
        self.data = data
        self.trackpath = trackpath  # path to the track

    @classmethod
    def read(cls, trackpath: str|Path) -> 'Track':
        """read the file at `trackpath` into a `Track`"""
        (rate, data), trackpath = read(trackpath)
        return Track(rate, data, trackpath)


    def write(self):
        """write `self` to `self.trackpath`"""
        if self.trackpath is None:
            raise ValueError(f"expected a path to write to, got '{self.trackpath}")
        if self.data is None:
            raise ValueError(f"expected data to write, got '{self.data}")
        write(self.trackpath, self.rate, self.data)
        return self

    def to_mono(self):
        if self.nchannels > 1:
            self.data = np.mean(self.data, axis=1)
            self.nchannels = 1
        return self

    def to_stereo(self):
        if self.nchannels == 2:
            pass
        elif self.nchannels == 1:
            # convert ndarray of shape (x, 1) into ndarray of shape (x, 2): [ [l1,r1],[l2,r2], ... ]
            self.data = self.data / 2
            self.data = np.transpose(np.vstack((self.data, self.data)))
            self.nchannels = 2
        else:
            raise NotImplementedError(f"'to_stereo' conversion not implemented for number of channels: '{self.nchannels}'")
        return self

    def resample(self, new_rate:int) -> 'Track':
        """resample to a new rate"""
        if new_rate != self.rate:
            # scikit's `resample` resamples to a specific number of frames, not to a sampling rate
            nframes = seconds_to_frame(
                frame_to_seconds(self.nframes, self.rate),
                new_rate
            )
            resampled: NDArray = resample(self.data, nframes)  # pyright: ignore
            assert resampled.shape[0] == nframes, f"wrong number of resampled frames: expected {nframes}, got {resampled.shape[0]}"
            self.data = resampled
            self.rate = new_rate
            self.nframes = nframes
        return self


class TrackList:

    tracklist: List[Track] = []
    rate: int

    def __init__(self, tracks: List[Track]):
        self.tracklist = tracks
        self.resample()

    def get_best_rate(self):
        if len(self.tracklist):
            return max(t.rate for t in self.tracklist)
        else:
            raise ValueError("TrackList.tracklist is empty")

    def resample(self) -> 'TrackList':
        """
        resample all tracks in 'TrackList' to the highest rate among these tracks
        """
        best_rate = self.get_best_rate()
        self.tracklist = [
            #TODO why doesn't it print
            t.resample(best_rate) for t in self.tracklist
        ]
        self.rate = best_rate
        return self

    def to_mono(self) -> "TrackList":
        self.tracklist = [ t.to_mono() for t in self.tracklist ]
        return self

    @classmethod
    def read_from_dir(cls, trackspath: str|Path) -> "TrackList":
        return TrackList([
            Track(rate, data, trackpath)
            for ((rate, data), trackpath)
            in read_from_dir(trackspath)
        ])




