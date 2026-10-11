import re

class Gen:
    nchunks: int,
    length: int,

    def __init__(
        nchunks: int,
        length: float,
        freq: str,
        dev: float | None = 0,
        outpath: str,
        overwrite: bool = False,
    ):
        ...

    def parse_freq(freq) -> list[int]:
        ...