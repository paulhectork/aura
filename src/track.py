from typing import Tuple

import numpy as np
from numpy.typing import NDArray


class Track():
    def __init__(self, samplerate: int, data: NDArray):
        if len(data.shape) == 1:
            nchannels = 1
        else:
            nchannels = data.shape[1]
        self.nchannels = nchannels
        self.samplerate = samplerate
        self.nframes = data.shape[0]  # number of frames in Track
        self.data = data

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