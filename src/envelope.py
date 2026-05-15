from typing import Tuple, List, Dict, Callable, Literal
from pathlib import Path
import random
import json
import re

import numpy as np

from src.utils.utils import get_random_item, array_plot
from src.utils.validate import validate_comparison, validate_float_isinrange, validate_type
from src.utils.io_op import fp_to_abs_validate, write_json, read_str, write_str, check_exists_file
from src.track import Track

def to_linear_function(a: Tuple[int|float, int|float], b: Tuple[int|float, int|float]) -> Callable[[int], float|float]:
    """
    generate a linear function from 2 points a and b.
    this function will be a multiplier that will be applied to a track.
    adapted from: https://www.geogebra.org/m/mdxgkgtd
    """
    x_a, y_a = a
    x_b, y_b = b
    slope = (y_b-y_a) / (x_b-x_a)
    intercept = y_a - slope * x_a  # y-offset when x=0. `slope * x_a` = the value of `y_a` if `intercept==0` => from there, we can calculate the intercept.
    # print(f"x: x*{slope} + {intercept}")
    return lambda x: x*slope + intercept


class Envelope:

    #NOTE a possible optimisation would be to internally represent the envelope as a 2D matrix of shape:
    # >>> [ [0, a_t, d_t,   1],    # start-attack-decay-sustain-end time, 0..1
    # ...   [0,   a,   d,   0] ]   # start-attack-decay-sustain-end volumes, 0..1
    # and then do numpy operations.

    curves_allowed = ["linear"]
    curve_default = "linear"

    def __init__(
        self,
        a:float,
        a_t:float,
        d:float,
        d_t:float,
        s_t: float,
        curve: str|None = None
    ):
        """
        ADSR envelope to apply to a prerecorded Track.

        an envelope is basically a curve that passes through 8 points:
        - (  0, 0), (a_t, a): attack phase
        - (a_t, a), (d_t, d): decay phase
        - (d_t, d), (s_t, d): sustain phase. sustain volume is equal to decay volume
        - (s_t, d), (  1, 0): release phase

        where x-coordinates are points in time and y-coordinates are audio volumes.
        volume and time are expressed in range 0..1:
            - volume: 0 = silent, 1 = 100% of track volume
            - time: 0 = start of track, 1 = end of track

        NOTE: attack starts at (0,0) (= start of track, silent) and release ends at (0,0) (end of track, silent).
        the main reason is that the calculation and application of a multiplier function
        gets much more complicated otherwise: the region where there is sound can be different
        from the dimensions of the track...

        :param a: attack volume
        :param d: decay volume
        :param a_t: attack time
        :param d_t: decay time
        :param s_t: sustain time. sustain volume is implicitly defined as equal to `d`
        :param curve: interpolation curve
        """
        try:
            # assert that all values are in 0..1 range
            for v in [ a, d, a_t, d_t, s_t ]:
                validate_float_isinrange(v, 0, 1, inclusive=True)
            # assert that times are correctly ordered
            for x1, x2 in ((0,a_t), (a_t,d_t), (d_t,s_t), (s_t,1)):
                assert x1<=x2
        except (AssertionError, ValueError):
            print(
                "invalid envelope: expected 0 <= a_t <= d_t and a <= 1 and d <= 1, got: {}"
                .format(json.dumps({ "a":a, "a_t":a_t, "d":d, "d_t":d_t, "s_t":s_t }))
            )

        # NOTE: other interpolation options: https://www.w3resource.com/numpy/snippet/numpy-interpolation-guide.php
        curve = self.curve_default if curve == None else curve
        if curve not in self.curves_allowed:
            raise NotImplementedError(f"invalid value for 'curve': expected one of {self.curves_allowed}, got '{curve}'")

        # sustain volume is the same as decay => cannot be set by user
        s = d

        self.a = a
        self.d = d
        self.s = d
        self.a_t = a_t
        self.d_t = d_t
        self.s_t = s_t
        self.curve = curve

        if self.curve == "linear":
            self.attack_mul = to_linear_function((0,0), (a_t,a))
            self.decay_mul = to_linear_function((a_t,a), (d_t,d))
            self.sustain_mul = to_linear_function((d_t,d), (s_t,s))
            self.release_mul = to_linear_function((s_t,s), (1,0))
        return

    @classmethod
    def random(cls) -> 'Envelope':
        """
        generate an envelope with random values
        """
        a_t, d_t, s_t = sorted([ random.random() for _ in range(0,3) ])
        return Envelope(
            a=1,
            d=random.uniform(0.5, 1.),
            a_t=a_t,
            d_t=d_t,
            s_t=s_t,
            curve=random.choice(cls.curves_allowed)
        )

    @classmethod
    def from_dict(cls, env:Dict) -> "Envelope":
        """
        load an envelope from a dict, with validation. useful when loading envelopes from file.
        to create an envelope without validation, use Envelope(**envelope_as_dict)
        """
        all_attrs = [ "a", "d", "a_t", "d_t", "s_t", "curve" ]  # all allowed keys

        env = validate_type(env, dict)

        env_keys = list(env.keys())
        # all non-optional parameters are in `env`
        missing_keys = [ k for k in all_attrs if k not in env_keys ]
        assert len(missing_keys) == 0, f"the following keys are missing from 'env': {missing_keys}"
        # all the keys from `env` are allowed
        forbidden_keys = [ k for k in env_keys if k not in all_attrs ]
        assert len(forbidden_keys) == 0, f"the following keys are not allowed in 'env': {forbidden_keys}"

        return Envelope(**env)

    def to_dict(self):
        return {
            "a": self.a,
            "d": self.d,
            "a_t": self.a_t,
            "d_t": self.d_t,
            "s_t": self.s_t,
            "curve": self.curve
        }

    def write(self, path:str|Path):
        write_json(path, self.to_dict())

    def get_mul_func(self, step_name: Literal["a","d","s","r"]) -> Callable:
        if step_name == "a":
            return self.attack_mul
        elif step_name == "d":
            return self.decay_mul
        elif step_name == "s":
            return self.sustain_mul
        elif step_name == "r":
            return self.release_mul
        return

    def make_multiplier(
        self,
        lin_func: Callable,
        track_step: np.ndarray,
        pct_start: float,
        pct_end: float,
    ) -> np.ndarray:
        """
        generate a multiplier for single envelope step (attack/decay/sustain/release) for the relevant part of a track.

        basically a multiplier is an ndarray of values in range 0..1 used to apply
        `self.(attack|decay|sustain|release)_mul`.
        the multiplier expands the *_mul functions (defined with 0 being the start of
        the track, 1 being the end) to have as many values as the track has frames.
        it will be used to multiply each value in `track_step.data`, thus applying the envelope.

        :param lin_func: a function generated from plotting a line between 2 points
        :param track_step: a slice of a numpy array
        :param pct_start: the start of track_step within the entire track in range 0..1
        :param pct_end: the end track_step within the entire track in range 0..1
        """
        indices = np.linspace(pct_start, pct_end, track_step.shape[0])
        multipliers = lin_func(indices)
        return multipliers

    def apply_step(
        self,
        lin_func: Callable,
        track_step: np.ndarray,
        pct_start: float,
        pct_end: float,
    ) -> np.ndarray:
        """
        generate and apply an envelope multiplier to the relevant slice of a track.
        """
        return track_step * self.make_multiplier(lin_func, track_step, pct_start, pct_end)

    def apply(self, track: Track) -> Track:
        """
        apply an envelope to a Track
        """
        envelope_data = [
            (self.attack_mul, 0, self.a_t),
            (self.decay_mul, self.a_t, self.d_t),
            (self.sustain_mul, self.d_t, self.s_t),
            (self.release_mul, self.s_t, 1)
        ]
        track_enveloped = np.concat(
            [
                self.apply_step(
                    lin_func,
                    track.get_range(pct_start, pct_end),
                    pct_start,
                    pct_end
                ) for lin_func, pct_start, pct_end in envelope_data
            ],
            axis=0
        )
        track.data = track_enveloped
        return track


class EnvelopeList:

    envlist: List[Envelope]

    def __init__(self, envlist:List[Envelope], overwrite: bool = False):
        for env in envlist:
            validate_type(env, Envelope)
        self.envlist = envlist
        self.overwrite = overwrite

    @classmethod
    def random(cls, n:int = 10) -> "EnvelopeList":
        """
        generate an EnvelopeList containing `n` random Envelopes
        """
        n = validate_type(n, int)
        validate_comparison("lt", 0, n)
        return EnvelopeList([
            Envelope.random()
            for _ in range(1, n+1)
        ])

    @classmethod
    def from_list(cls, envlist:List[Dict]) -> "EnvelopeList":
        envlist = validate_type(envlist, list)
        return EnvelopeList([
            Envelope.from_dict(env)
            for env in envlist
        ])

    def to_list(self) -> List[Dict]:
        """
        convert EnvelopeList as a List of Dicts
        """
        return [
            env.to_dict() for env in self.envlist
        ]

    @classmethod
    def read(cls, fp: str|Path) -> 'EnvelopeList':
        """
        read and parse the env list an d return is as an EnvelopeList.
        we expect "\n"-separated envelopes representing dicts
        """
        fp = fp_to_abs_validate(fp)

        empty_line = re.compile(r"^\s*$")
        data = read_str(fp)
        envlist_list = [
            json.loads(l)
            for l in data.split("\n")
            if not empty_line.search(l)
        ]

        return EnvelopeList.from_list(envlist_list)

    def write(self, fp:Path|str) -> 'EnvelopeList':
        check_exists_file(fp, self.overwrite)
        write_str(fp, "\n".join(json.dumps(d) for d in self.to_list()))
        return self

    def get_one(self) -> Envelope:
        return get_random_item(self.envlist)


def random_envs_to_file(n:int, fp: str|Path, overwrite: bool) -> None:
    envlist = EnvelopeList.random(n)
    envlist.overwrite = overwrite
    envlist.write(fp)
