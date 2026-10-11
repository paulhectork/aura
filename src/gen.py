import re
from pathlib import Path
from typing import Literal

import numpy as np

from src.base import Base
from src.track import Track
from src.utils.validate import validate_isinlist, validate_pretty, validate_type

re_freq = re.compile(r"^\d+(:\d+)$")

class Gen(Base):
    """
    generate `nchunks` instances of a sound and save it to an output directory.
    sounds are generated using `gen_*` functions. currently implemented are:
    - `gen_sine`: generate a sine based on a frequency range.
    """

    allowed_soundtypes = ["sine"]

    soundtype: Literal["sine"]
    nchunks: int
    freq: list[int]
    length: int
    dev: int
    outpath: Path

    def __init__(
        self,
        soundtype,
        nchunks: int,
        length: float,
        freq: str,
        outpath: str,
        dev: float | None = 0,
        overwrite: bool = False,
        visualize: bool = False,
    ):
        # maps a value of `soundtype` to a sound generation function
        gen_func_mapper = {
            "sine": self.gen_sine
        }

        validate_pretty("soundtype", validate_isinlist, i=soundtype, vallist=self.allowed_soundtypes)

        super().__init__(
            action="gen",
            outpath=outpath,
            outpath_type="dir",
            length=length,
            dev=dev,
            nchunks=nchunks,
            nchannels=1,
            overwrite=overwrite
        )

        self.freq = self.parse_freq(freq)
        self.visualize = visualize
        self.soundtype = soundtype
        # function used to generate chunks of sound
        self.gen_func = gen_func_mapper[self.soundtype]
        # pipulated in `self.gen`
        self.chunks = []


    @staticmethod
    def parse_freq(freq) -> list[int]:
        if not re_freq.match(freq):
            raise ValueError(f"'freq' must be of shape: 'n(:n)?', with 'n' a positive integer. examples: '400:1000', '400'")

        freq_list = []
        for f in freq.split(freq):
            validate_pretty("freq", validate_type, i=f, type_=int)
            f = int(f)
            freq_list.append(f)

        return freq_list

    def gen_sine(self) -> np.ndarray:
        # INSPO:
        # - https://gist.github.com/yuchen-xue/67b7fb72b6ae418d43b10cca2ebda153
        # - https://zach.se/generate-audio-with-python/
        # - https://stackoverflow.com/questions/67085963/generate-colors-of-noise-in-python
        #
        ...

    def gen_one(self, i: int) -> Track:
        data = self.gen_func()
        return Track(rate=self.rate, data=data, trackpath=self.to_outpath(i, self.soundtype))

    def gen(self):
        for i, _ in enumerate(range(self.nchunks)):
            self.chunks.append(self.gen_one(i))
        return self

    def pipeline(self) -> "Gen":
        self.gen().write_chunks()
        return self

