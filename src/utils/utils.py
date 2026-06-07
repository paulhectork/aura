from typing import List
import random

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


def get_random_item(l: List):
    return random.choice(l)


def to_mono(data: np.ndarray) -> np.ndarray:
    """
    convert a multichannel track to mono.
    input shape  : (samples, nchannels) (nchannels = the number of channels in the track)
    output shape : (samples,)
    """
    if len(data.shape) > 1 and data.shape[1] > 1:
        dtype_orig = data.dtype
        # NOTE: we do extra type conversions to avoid distorsions when converting to/from mono
        # when converting to mono, we upcast as Float32;
        # at the end of the coversion, we downcast back to data's `dtype`.
        # this is because mean will sum up the left and right channels
        # which can cause dtype overflow: numbers larger than their original dtype.
        # i.e., Int16 is in range (−32768 to 32767) => convert to Float32 to avoid distorsion
        data = np.mean(data.astype(np.float32), axis=1).astype(dtype_orig)
    return data


def to_stereo(data: np.ndarray) -> np.ndarray:
    """
    convert a multidimensionnal array to stereo.
    input shape  : (samples, nchannels) or (samples,) (nchannels = the number of channels in the track)
    output shape : (samples, 2)
    """
    nchannels = data.shape[1] if len(data.shape) > 1 else 1
    dtype_orig = data.dtype

    # aldready in stereo
    if nchannels == 2:
        return data

    # mono to stereo
    elif nchannels == 1:
        # convert np.ndarray of shape (x, 1) into np.ndarray of shape (x, 2)
        # the `astype` dtype conversion is to avoid dtype overflow that
        # may be caused by intermediate operations. see note in `to_mono`.
        data = np.stack((data, data), axis=1).astype(dtype_orig)

    # multichannel to stereo
    elif nchannels > 2:
        # avoid dtype overflow
        data = data.astype(np.float32)  # shape: (samples, nchannels)
        # 1. compute per-channel pan weights
        # channel 0 is 100% L, channel n-1 is 100% R
        r_pan = np.linspace(0, 1, nchannels)  # shape: (nchannels,)
        l_pan = 1 - r_pan                     # shape: (nchannels,)
        print(l_pan, r_pan)
        # 2. apply panning: multiply each channel by its L/R weights
        # np.sum is applied along each channel. 2 ndarrays are generated:
        # 1 for the left track, 1 for the right
        l = np.sum(data * l_pan, axis=1)  # shape: (samples,)
        r = np.sum(data * r_pan, axis=1)  # shape: (samples,)
        # 3. normalize to avoid clipping on the cast back
        peak = np.max(np.abs(np.stack([l, r])))
        max_val = np.iinfo(dtype_orig).max if np.issubdtype(dtype_orig, np.integer) else 1.0
        if peak > max_val:
            l, r = l * (max_val / peak), r * (max_val / peak)
        data = np.stack((l, r), axis=1).astype(dtype_orig)
        return data

    # invalid data array (0 or less channels)
    else:
        raise NotImplementedError(f"'to_stereo' conversion not implemented for number of channels: '{nchannels}'")
    return data


def array_plot(
    a: np.ndarray,
    stack: bool = True
):
    """
    `a` is a 1D or 2D array.
    if stack, combine all ndarrays in a.shape[0] in a single plot
    otherwise, create as many subplots as a.shape[1] => 2 subplots for a stereo track
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is only available if `dev` packages are installed !")

    # f it's a 2D array, stack all axes. if it's a 1D array, splitting over subplots is useless
    if stack or len(a.shape) == 1:
        plt.plot(a)
    else:
        n = a.shape[1]
        fig, axs = plt.subplots(n)
        for i in range(n):
            print(i)
            axs[i].plot(a[:,i])
            axs[i].grid(True)

    plt.grid(True)
    plt.show()