from typing import Tuple, List, Dict, Callable
from ast import literal_eval
from pathlib import Path
import random
import json
import re

from src.utils.validate import validate_comparison, validate_float_isinrange, validate_type
from src.utils.io_op import fp_to_abs_validate, write_json, read_str, write_str, check_exists_file
from src.track import Track


def to_linear_function(a: Tuple[int|float, int|float], b: Tuple[int|float, int|float]) -> Callable[[int], float|float]:
    """
    generate a linear function from 2 points a and b.
    adapted from: https://www.geogebra.org/m/mdxgkgtd
    """
    a_x, a_y = a
    b_x, b_y = b
    slope = (b_y - a_y) / (b_x - a_x)
    intercept = a_y - slope * a_x  # y-offset when x=0. `slope * a_x` = the value of `a_y` if `intercept==0` => from there, we can calculate the intercept.
    return lambda x: x*slope + intercept


class Envelope:

    #NOTE a possible optimisation would be to internally represent the envelope as a 2D matrix of shape:
    # >>> [ [0, a_t, d_t, s_t],    # start-attack-decay-sustain-end time, 0..1
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
        s_t:float=0,
        curve: str|None = None
    ):
        """
        envelope to apply to a prerecorded Track.

        volume is expressed in range 0..1: 0 = silent, 1 = 100% of track volume
        time is expressed in range 0..1: 0 = start of track, 1 = end of track
        there is no sustain volume parameter: sustain volume is the same as decay volume

        :param a: attack volume
        :param d: decay volume
        :param a_t: attack time
        :param d_t: decay time
        :param s_t: sustain time
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
                "invalid envelope: expected 0 <= a_t <= d_t <= st <=1 and a <= 1 and s <= 1, got: {}"
                .format(str({ a:a, a_t:a_t, d:d, d_t:d_t, s_t:s_t }))
            )

        curve = self.curve_default if curve == None else curve
        if curve not in self.curves_allowed:
            raise NotImplementedError(f"invalid value for 'curve': expected one of {self.curves_allowed}, got '{curve}'")

        self.a = a
        self.d = d
        self.a_t = a_t
        self.d_t = d_t
        self.s_t = s_t
        self.curve = curve

        # TODO do as a matrix multiplication or as a numpy interpolation ?
        # https://numpy.org/doc/stable/reference/generated/numpy.interp.html
        if self.curve == "linear":
            self.attack = to_linear_function((0,0), (a_t,a))
            self.decay = to_linear_function((a_t,a), (d_t,d))
            self.sustain = to_linear_function((d_t,d), (s_t,0))
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

    def apply_attack_interp(self, track: Track) -> Track:
        i = track.get_frame_index(self.a_t, True)
        return track

    def apply(self, track: Track) -> Track:
        """
        apply an envelope to a Track
        """
        # todo
        return track


# TODO check for overwrites
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
        write_str(fp, "\n".join(str(d) for d in self.to_list()))
        return self

def random_envs_to_file(n:int, fp: str|Path, overwrite: bool) -> None:
    envlist = EnvelopeList.random(n)
    envlist.overwrite = overwrite
    envlist.write(fp)
