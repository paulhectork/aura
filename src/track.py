from typing import Tuple

import numpy as np


class Track():
    def __init__(self, data: Tuple[int, np.ndarray]):
        if len(data[1].shape) == 1:
            nchannels = 1
        else:
            nchannels = data[1].shape[1]

        self.samplerate = data[0]
        self.nchannels = nchannels
        self.nframes = data[1].shape[0]  # number of frames in Track
        self.data = data[1]

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