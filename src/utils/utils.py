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
    return frame / samplerate

