from pathlib import Path

from src.utils.io_op import make_dir
from src.utils.utils import seconds_to_frame, get_chunk_ends, trailing_zeroes
from src.utils.validate import validate_type, validate_isinlist, validate_comparison, validate_pretty


class Base:
    """base class holding utils for common arguments"""

    def __init__(self, **kwargs):
        """
        parametrers: (passed as kwargs)
            action: str,
            outpath: str | Path,
            nchunks: int,
            length: float,
            dev: float | None = 0,
            overwrite: bool = False,
            rate: int = True
        """
        action = kwargs.pop("action")
        length = kwargs.pop("length")
        nchunks = kwargs.pop("nchunks")
        dev = kwargs.pop("dev")
        rate = kwargs.pop("rate")
        outpath = kwargs.pop("outpath")
        overwrite = kwargs.pop("overwrite")

        outpath = make_dir(outpath, overwrite)  # pyright: ignore
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
        self.length = length
        self.dev = dev
        self.rate = rate

    def write_chunks(self):
        """
        write self.chunks to outpath folder (self.chunks is an array of `Track`s)
        """
        chunks = getattr(self, "chunks")
        if not chunks:
            raise AttributeError("undefined attribute: chunks")
        for chunk in chunks:
            chunk.write()
        print()
        print(f"aura::{self.action}: output chunks saved to: {self.outpath}")

