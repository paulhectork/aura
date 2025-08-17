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
        return self