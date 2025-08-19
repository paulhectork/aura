import numpy as np
from numpy.typing import NDArray


def seconds_to_frame(time:float, rate:int) -> int:
    """
    convert a time in seconds to a specific frame given a rate
    (e.g. get the frame at 1.8s in 44100hz)

    :param time: time in seconds
    :param rate: sample rate to convert to
    """
    return round(time * rate)


def frame_to_seconds(frame: int, rate:int) -> float:
    """
    convert a frame at a given rate to a time in seconds

    :param frame: frame in a given rate
    :param rate: the sample rate of frame
    """
    return frame / rate


def get_chunk_ends(chunk_starts: NDArray, chunk_lengths: NDArray) -> NDArray:
    """
    from 2 1D-arrays (one with start position of each chunk, the other length of each chunk), return an array of end position of each chunk
    """
    return np.sum([chunk_starts, chunk_lengths], axis=0)

def trailing_zeroes(i:int, total:int)-> str:
    """
    in an iterator of size `total`, at iteration `i`, return a pretty-printed string indicating the iteration number with trailing `0`:
    i=10, total=999 => 010
    i=55, total=999 => 055
    """
    # add trailing zeroes to `i` for prettier filename formatting
    num_zeroes = len(str(total)) - len(str(i))
    return f"{'0'*num_zeroes}{i}"
