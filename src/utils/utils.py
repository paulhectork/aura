import numpy as np
from numpy.typing import NDArray


def seconds_to_frame(time:float, samplerate:int) -> int:
    """
    convert a time in seconds to a specific frame given a samplerate
    (e.g. get the frame at 1.8s in 44100hz)

    :param time: time in seconds
    :param samplerate: sample rate to convert to
    """
    return round(time * samplerate)


def frame_to_seconds(frame: int, samplerate:int) -> int:
    """
    convert a frame at a given samplerate to a time in seconds

    :param frame: frame in a given samplerate
    :param samplerate: the sample rate of frame
    """
    return round(frame / samplerate)


def get_chunk_ends(chunk_starts: NDArray, chunk_lengths: NDArray) -> NDArray:
    """
    from 2 1D-arrays (one with start position of each chunk, the other length of each chunk), return an array of end position of each chunk
    """
    return np.sum([chunk_starts, chunk_lengths], axis=0)
