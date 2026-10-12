import re
import random
from pathlib import Path
from typing import Literal, Callable

import numpy as np
from tqdm import tqdm

from src.base import Base
from src.track import Track
from src.utils.utils import seconds_to_frame, array_plot
from src.utils.validate import validate_float_isinrange, validate_isinlist, validate_pretty, validate_type

re_freq = re.compile(r"^\d+(:\d+)?$")


def noise_psd(n: int, psd: Callable = lambda f: 1) -> np.ndarray:
    """
    generate `n` noise samples along a power spectrum distribution `psd`
    (distribution of power for each frequency)
    used to create different colors of noise.
    :param n: number of samples to generate
    :param psd: power spectrum distribution along which to generate noise
    """
    # white noise spectrum
    x_white = np.fft.rfft(np.random.randn(n));
    # gain for each frequency bin
    # (since we are using a fourier transform, we don't have a continuous list of frequency, but an array of frequency bins, which are different slots in the fourier transform)
    s = psd(np.fft.rfftfreq(n))
    # normalize s so that each noise color has the same perceived voluem as white noise
    # in technical terms, we rescale gains so their root-mean-square is 1
    s = s / np.sqrt(np.mean(s**2))
    # multiply each frequency by its gain
    x_shaped = x_white * s;
    # convert the sample back to n time-domain samples => return the actual samples for the noise.
    return np.fft.irfft(x_shaped);


def psd_generator(f: Callable) -> Callable:
    """
    decorator around `noise_psd`: takes a psd function
    and returns a function that will generate `n` samples of noise

    usage:
    - psd_generator must be applied to a function that takes as an input an ndarray of frequencies
    - functions decorated must be called with `decorated_function(number_of_samples)`
    """
    return lambda n: noise_psd(n, f)


class Gen(Base):
    """
    generate `nchunks` instances of a sound and save it to an output directory.
    sounds are generated using `gen_*` functions. currently implemented are:
    - `gen_sine`: generate a sine based on a frequency range.
    """

    allowed_soundtypes = [
        "sine",
        "white-noise",
        "pink-noise",
        "brownian-noise",
        "blue-noise",
        "violet-noise",
        "random-noise",
        "random"
    ]

    # values of `soundtype` for which the argument `freq` is required
    needs_freq = ["sine", "random"]

    soundtype: Literal["sine", "white-noise", "pink-noise", "brownian-noise", "blue-noise", "violet-noise"]
    nchunks: int
    freq: list[int] | None
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
        sine_to_noise: float|None = None,
        dev: float | None = 0,
        overwrite: bool = False,
        visualize: bool = False,
    ):
        # maps a value of `soundtype` to a sound generation function
        gen_func_mapper = {
            "sine": self.gen_sine,
            "white-noise": self.gen_white_noise,
            "pink-noise": self.gen_pink_noise,
            "brownian-noise": self.gen_brownian_noise,
            "blue-noise": self.gen_blue_noise,
            "violet-noise": self.gen_violet_noise,
            "random-noise": self.gen_random_noise,
            "random": self.gen_random
        }

        validate_pretty("soundtype", validate_isinlist, i=soundtype, vallist=self.allowed_soundtypes)

        if sine_to_noise:
            validate_pretty("soundtype", validate_float_isinrange, min_=0, max_=1, inclusive=True)

        # mono only for this
        nchannels = 1

        super().__init__(
            action="gen",
            outpath=outpath,
            outpath_type="dir",
            length=length,
            dev=dev,
            nchunks=nchunks,
            nchannels=nchannels,
            overwrite=overwrite
        )

        self.noise_gens = [
            self.gen_white_noise,
            self.gen_pink_noise,
            self.gen_brownian_noise,
            self.gen_blue_noise,
            self.gen_violet_noise,
        ]
        self.all_gens = self.noise_gens + [self.gen_sine]

        self.visualize = visualize
        self.soundtype = soundtype
        # frequency is only useful if we'll generate sines
        if soundtype in self.needs_freq:
            self.freq = self.parse_freq(freq)
        else:
            self.freq = None
        # length of each chunk to generate, in number of frames, with standard deviation applied
        self.chunk_lengths = self.compute_chunk_lengths()
        # function used to generate chunks of sound
        self.gen_func = gen_func_mapper[self.soundtype]
        # populated in `self.gen`
        self.chunks = []

        if self.soundtype == "random":
            if sine_to_noise:
                # user defined distribution
                self.sine_to_noise = sine_to_noise
            else:
                # nornal distribution:
                # number of sine generating functions / number of noise generating functions
                self.sine_to_noise = 1 / len(self.noise_gens)

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

    def gen_white_noise(self, chunk_length: int) -> np.ndarray:
        """
        white noise = linear gain over all frequencies
        """
        @psd_generator
        def white_noise(f: np.ndarray) -> int:
            # `f` is an ndarray of frequencies over which to compute a psd. it is passed implicitly by `psd_generator`
            # equal power for all frequencies
            return 1
        return white_noise(chunk_length)

    def gen_pink_noise(self, chunk_length: int) -> np.ndarray:
        """
        linear gain in logarithmic scale
        => equal power in the frequency range from 40 to 60 Hz as in the band from 4000 to 6000 Hz
        => perceptually uniform to the human ear
        """
        @psd_generator
        def pink_noise(f: np.ndarray) -> np.ndarray:
            # `f` is an ndarray of frequencies over which to compute a psd. it is passed implicitly by `psd_generator`
            # f -> 1/f**2 if frequency > 0:
            # f -> 1/inf -> 0, if frequency == 0
            return 1/np.where(f == 0, float('inf'), np.sqrt(f))
        return pink_noise(chunk_length)

    def gen_brownian_noise(self, chunk_length: int) -> np.ndarray:
        """
        brownian noise, or 1/f noise has a power density that decreases 6.02 dB per octave
        """
        @psd_generator
        def brownian_noise(f: np.ndarray) -> np.ndarray:
            # `f` is an ndarray of frequencies over which to compute a psd. it is passed implicitly by `psd_generator`
            # 1/f if `f` > 0
            # 1/inf => 0 otherwise
            return 1/np.where(f == 0, float('inf'), f)
        return brownian_noise(chunk_length)

    def gen_violet_noise(self, chunk_length: int) -> np.ndarray:
        """
        power density increases 6.02 dB per octave with increasing frequency
        """
        @psd_generator
        def violet_noise(f: np.ndarray) -> np.ndarray:
            # `f` is an ndarray of frequencies over which to compute a psd. it is passed implicitly by `psd_generator`
            # f -> f
            return f
        return violet_noise(chunk_length)

    def gen_blue_noise(self, chunk_length: int) -> np.ndarray:
        """
        blue noise's power density increases 3.1 db per octave
        """
        @psd_generator
        def blue_noise(f: np.ndarray) -> np.ndarray:
            # `f` is an ndarray of frequencies over which to compute a psd. it is passed implicitly by `psd_generator`
            # f -> f**2
            return np.sqrt(f)
        return blue_noise(chunk_length)

    def gen_random_noise(self, chunk_length: int) -> np.ndarray:
        """
        for each chunk, select a noise function for which to generate sound
        """
        func = random.choice(self.noise_gens)
        return func(chunk_length)

    def gen_sine(self, chunk_length: int) -> np.ndarray:
        """
        chunk_length: # of samples to generate as an int
        adapted from https://gist.github.com/yuchen-xue/67b7fb72b6ae418d43b10cca2ebda153
        """
        if not self.freq:
            raise ValueError(f"with `soundtype=='sine'`, `freq` must be defined (got `freq={self.freq}`)")
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

    def gen_random(self, chunk_length: int) -> np.ndarray:
        # todo move to init
        sine_to_noise = int(self.sine_to_noise * 100)
        noise_to_sine = 100 - sine_to_noise
        gens = [self.gen_sine for _ in range(sine_to_noise)]
        assert len(gens) == sine_to_noise
        gens += random.choices(self.noise_gens, k=noise_to_sine)
        assert len(gens) == 100
        return random.choice(gens)(chunk_length)

    def gen_one(self, i: int, chunk_length: int) -> Track:
        """
        :param i: position of currently generated chunk in `self.chunks` (array of all generated chunks)
        :param chunk_length: # of samples to generate as an int
        """
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

