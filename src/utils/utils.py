from typing import List
import random

import numpy as np


def trailing_zeroes(i:int, total:int)-> str:
    """
    in an iterator of size `total`, at iteration `i`, return a pretty-printed string indicating the iteration number with trailing `0`:
    i=10, total=999 => 010
    i=55, total=999 => 055
    """
    # add trailing zeroes to `i` for prettier filename formatting
    num_zeroes = len(str(total)) - len(str(i))
    return f"{'0'*num_zeroes}{i}"


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


def get_chunk_ends(chunk_starts: np.ndarray, chunk_lengths: np.ndarray) -> np.ndarray:
    """
    from 2 1D-arrays (one with start position of each chunk, the other length of each chunk), return an array of end position of each chunk
    """
    return np.sum([chunk_starts, chunk_lengths], axis=0)


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
    input shape  : (samples, nchannels?) (nchannels = the number of channels in the track)
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


def apply_width(data: np.ndarray, width: float, crackle: bool = False) -> np.ndarray:
    """
    mostly copied from `adjust_width` here: https://www.sbehrens4d.com/posts/python_dsp_1_panning.html

    :param w: the width, in range 0..1, inclusive:
        0   => left and right channels are centered => 0% stereo space => mono
        0.5 => left channel is panned at 50%L, right channel panned at 50%R => 50% stereo space
        1   => hard panning (L is 100%L, R is 100%R) => 100% stereo space
    :param data:
        input shape of data  : (samples, 2)
        output shape of data : (samples, 2)
    :param crackle: if `True`, avoid retyping to float32 before retyping. this will add some nice clipping'n'crackling.
    """
    dtype_orig = data.dtype
    shape_orig = data.shape

    # convert to float32 for less clipping. only useful on `l` and `r , will be propagated in all other calculations
    retype = lambda x: x.astype(np.float32) if not crackle else x

    # if not crackle, return. if crackle, process `data`. this will not modify its width but add more clipping.
    if width == 1 and not crackle:
        return data
    # get left and right channels
    l = retype(data[:,0])
    r = retype(data[:,1])
    # compute rescaled mid and side channels
    data_m = (l + r) * 0.5
    data_s = (l - r) * 0.5
    # compute rescaled mid-side basis
    e_m = np.array([[1],[1]])
    e_s = np.array([[1],[-1]])
    # compute mid and side signals (sound in center + sound in L/R)
    data_mid = data_m * e_m
    data_side = data_s * e_s
    # compute adjusted signal
    data_adjusted = data_mid + width * data_side

    # data_adjusted now is of shape (n_channels, samples) (1 array for left channel, 1 array for right channel)
    # => transpose back to (samples, n_channels) ([[L,R], [L,R]])
    # retype to dtype_orig to avoid crazy distorsion
    data = np.transpose(data_adjusted).astype(dtype_orig)
    assert np.equal(shape_orig, data.shape).all(), f"shape changed in processing. input: {shape_orig}, output: {data.shape}"
    return data


def apply_pan(pos: float, data:np.ndarray) -> np.ndarray:
    """
    copied from `mono_pan` here: https://www.sbehrens4d.com/posts/python_dsp_1_panning.html
    place a mono audio signal in the stereo field.

    :param pos: position in the stereo field, encoded as a float in range -1..1
    :param data: mono audio chunk represented by a 1d ndarray.
    """
    PI = np.pi
    SQRT12 = np.sqrt(0.5)
    dtype_orig = data.dtype

    def compute_panning_coeffs():
        # center panning
        if pos == 0:
            rho = lam = SQRT12
        # hard left panning
        elif pos == -1:
            lam, rho = 1, 0
        # hard left panning
        elif pos == 1:
            lam, rho = 0, 1
        # intermediate panning
        else:
            # compute angle
            alpha = (pos + 1) / 4 * PI
            # infer coefficients
            lam = np.cos(alpha)
            rho = np.sin(alpha)
        return lam, rho

    # make sure x_m is a mono signal
    if not (type(data) == np.ndarray and data.ndim == 1):
        raise ValueError("input must be a 1d numpy array.")
    # get panning coefficients
    lam, rho = compute_panning_coeffs()
    # compute panned signal
    data = np.array([[lam],[rho]]) * data
    data = np.transpose(data).astype(dtype_orig)
    return data


def fade(d1: np.ndarray, d2: np.ndarray) -> np.ndarray:
    """
    fade out d1, fade in d2 and return the result as a single ndarray
    input shapes: (samples, nchannels?)
    output shape: (samples, nchannels?)
    """
    assert np.equal(d1.shape, d2.shape).all(), f"incompatible shaoes. d1: {d1.shape}, d2: {d2.shape}"
    l = d2.shape[0]
    fin = np.linspace(0, 1, l)
    fout = 1 - fin
    if d1.ndim == 2:
        fin  = fin[:, np.newaxis]   # (samples,) -> (samples, 1) => broadcasts over nchannels
        fout = fout[:, np.newaxis]
    data = d1 * fout + d2 * fin
    return data


def is_1darray(d: np.ndarray) -> bool:
    return len(d.shape) == 1


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
            axs[i].plot(a[:,i])
            axs[i].grid(True)

    plt.grid(True)
    plt.show()