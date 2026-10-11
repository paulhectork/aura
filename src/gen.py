import re
import random
from pathlib import Path
from typing import Literal

import numpy as np
from tqdm import tqdm

from src.base import Base
from src.track import Track
from src.utils.utils import seconds_to_frame, array_plot
from src.utils.validate import validate_isinlist, validate_pretty, validate_type

re_freq = re.compile(r"^\d+(:\d+)?$")

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

        # mono only for this
        nchannels = 1

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
        # length of each chunk to generate, in number of frames, with standard deviation applied
        self.chunk_lengths = self.compute_chunk_lengths()
        # function used to generate chunks of sound
        self.gen_func = gen_func_mapper[self.soundtype]
        # populated in `self.gen`
        self.chunks = []

    @staticmethod
    def parse_freq(freq) -> list[int]:
        def to_int_ok(x):
            try:
                return int(x)
            except:
                return False

        if not freq or not re_freq.match(freq):
            raise ValueError(f"'freq' must be of shape: 'n(:n)?', with 'n' a positive integer. examples: '400:1000', '400'. (got: freq='{freq}')")

        return sorted([f_ for f in freq.split(":") if (f_ := to_int_ok(f))])

    def gen_sine(self, chunk_length) -> np.ndarray:
        """
        adapted from https://gist.github.com/yuchen-xue/67b7fb72b6ae418d43b10cca2ebda153
        """
        if len(self.freq) > 1:
            _freq = random.randint(*self.freq)
        else:
            _freq = self.freq[0]
        # points at which to sample the sine wave. frame indices are
        # converted to seconds, so the phase is correct in Hz
        positions = np.arange(chunk_length) / self.rate
        # 0..1: maximum amplitude
        amp = 1
        # the sine wave
        data = amp * np.sin(
            # computes a phase angle for each position
            2 * np.pi * _freq * positions
        )
        return data

    def gen_one(self, i: int, chunk_length) -> Track:
        data = self.gen_func(chunk_length=chunk_length)
        return Track(rate=self.rate, data=data, trackpath=self.to_outpath(i, self.soundtype))

    def gen(self):
        for i, chunk_length in tqdm(
            enumerate(self.chunk_lengths),
            desc=f"generating {self.soundtype}",
            total=self.nchunks
        ):
            self.chunks.append(self.gen_one(i, chunk_length))
        return self

    def pipeline(self) -> "Gen":
        self.gen().write_chunks()
        return self

