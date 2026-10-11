from pathlib import Path

from src.utils.io_op import make_dir, check_exists_file
from src.utils.utils import DEFAULT_RATE, frame_to_seconds, seconds_to_frame, get_chunk_ends, trailing_zeroes
from src.utils.validate import validate_type, validate_isinlist, validate_comparison, validate_pretty


# TODO add 2 subclasses to base ?
#   - one for when a single output track is generated (splice, skip)
#   - one for when an array of output tracks are generated (split, gen)
# right now, `Base` handle both cases but this might make its API a tad messy.
class Base:
    """base class holding utils for common arguments"""

    def __init__(self, **kwargs):
        """
        not all subclasses need to implement all properties. so far, this class
        just mutualizes properties and functions used by several files.

        parameters:
        ------------
        (passed as kwargs)
            action: str - used for message printing
            outpath: str | Path - path to output file or directory
            outpath_type: Literal["dir"|"file"]
            overwrite: bool = False - overwrite output file or directory
            nchannels: 1 | 2 - number of channels in output track (may be None)
            nchunks: int - number of chunks to generate (if task requires)
            length: float - length of output track or chunks (in seconds, then converted to # of frames)
            dev: float | None = 0 - standard deviation from length (if task requires. in seconds, then converted to # of frames)
            rate: int - framerate of data to generate
        """
        action = kwargs.pop("action")
        length = kwargs.pop("length")
        rate = kwargs.pop("rate", DEFAULT_RATE)
        outpath = kwargs.pop("outpath")
        outpath_type = kwargs.pop("outpath_type")
        overwrite = kwargs.pop("overwrite")
        nchannels = kwargs.pop("nchannels", None)
        nchunks = kwargs.pop("nchunks", None)
        dev = kwargs.pop("dev", None)

        assert outpath_type in ("dir", "file")
        if outpath_type == "dir":
            outpath = make_dir(outpath, overwrite)  # pyright: ignore
        else:
            outpath, _ = check_exists_file(outpath, overwrite)

        if nchannels:
            validate_pretty("nchannels", validate_isinlist, i=nchannels, vallist=[1,2])
        length = validate_pretty("length", validate_type, i=length, type_=float)
        if nchunks is not None:
            nchunks = validate_pretty("nchunks", validate_type, i=nchunks, type_=int)
        if dev is not None:
            dev = validate_pretty("dev", validate_type, i=dev, type_=float)

        length = seconds_to_frame(length, rate)
        dev = 0 if dev is None else float(dev)
        dev = seconds_to_frame(dev, rate)

        # splice / split / gen / ...
        self.action = action
        self.overwrite = overwrite
        self.outpath = outpath
        self.nchunks = nchunks
        self.nchannels = nchannels
        self.rate = rate
        self.length = length
        self.length_seconds = frame_to_seconds(length, self.rate)
        self.dev = dev

    def to_outpath(self, i:int, base: str) -> Path:
        """
        when generating an array of chunks (`self.chunks`), generate an
        outpath track name for a chunk
        :param i: the position of this chunk in the `self.chunk` array
        :param base: prefix of the track name
        """
        i = trailing_zeroes(i, self.nchunks)  # pyright:ignore
        trackname = f"{base}_chunk{i}.wav"
        return self.outpath.joinpath(trackname)


    def write_chunks(self):
        """
        when generating an array of chunks (`self.chunks`),
        write self.chunks to outpath folder (self.chunks is an array of `Track`s)
        """
        chunks = getattr(self, "chunks")
        if not chunks:
            raise AttributeError("undefined attribute: chunks")
        for chunk in chunks:
            # chunk is a Track
            chunk.write()
        print()
        print(f"aura::{self.action}: output chunks saved to: {self.outpath}")

