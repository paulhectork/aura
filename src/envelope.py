from typing import List, Dict
from ast import literal_eval
from pathlib import Path
import random
import json
import re

from .utils.validate import validate_float_isinrange, validate_type
from .utils.io_op import fp_to_abs_validate

class Envelope:

    curves_allowed = ["linear"]
    curves_default = "linear"

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
        for v in [ a, d, a_t, d_t, s_t ]:
            validate_float_isinrange(v, 0, 1, inclusive=True)
        curve = self.curves_default if curve == None else curve
        if curve not in self.curves_allowed:
            raise NotImplementedError(f"invalid value for 'curve': expected one of {self.curves_allowed}, got '{curve}'")

        self.a = a
        self.d = d
        self.a_t = a_t
        self.d_t = d_t
        self.s_t = s_t
        self.curve = curve

    @classmethod
    def random(cls) -> 'Envelope':
        """
        generate an envelope with random values
        """
        a_t, d_t, s_t = sorted([ random.random() for _ in range(0,2) ])
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
        obl_attrs = [ "a", "d", "a_t", "d_t", "s_t" ]  # non-optional keys

        env = validate_type(env, dict)

        env_keys = list(env.keys())
        # all non-optional parameters are in `env`
        missing_keys = [ k for k in obl_attrs if k not in env_keys ]
        assert len(missing_keys) == 0, f"the following keys are missing from 'env': {missing_keys}"
        # all the keys from `env` are allowed
        forbidden_keys = [ k for k in env_keys if k not in all_attrs ]
        assert len(forbidden_keys) == 0, f"the following keys are not allowed in 'env': {forbidden_keys}"
        if "curve" not in env_keys:
            env["curve"] = cls.curves_default

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


class EnvelopeList:

    envlist: List[Envelope]

    def __init__(self, envlist:List[Envelope]):
        assert all(isinstance(env, Envelope) for env in envlist), \
            f"all items from 'envlist' must belong to class 'Envelope', got {set(type(env) for env in envlist)}"
        self.envlist = envlist

    @classmethod
    def random(cls, n:int = 10) -> "EnvelopeList":
        """
        generate an EnvelopeList containing `n` random Envelopes
        """
        n = validate_type(n, int)
        return EnvelopeList([
            Envelope.random()
            for _ in range(1, n)
        ])

    @classmethod
    def read(cls, fp: str|Path) -> 'EnvelopeList':
        fp = fp_to_abs_validate(fp)

        # first, try to read it as a JSON. else, try to read it as a text file:
        # if it's a text-file, we expect "\n"-separated envelopes representing dicts
        empty_line = re.compile(r"^\s*$")
        with open(fp, mode="r") as fh:
            data = str(fh.read())
        try:
            envlist_dict = json.loads(data)
            if isinstance(envlist_dict, dict):
                envlist_dict = [envlist_dict]
        except json.JSONDecodeError:
            envlist_dict = [
                literal_eval(l)
                for l in data.split("\n")
                if not empty_line.search(l)
            ]

        envlist = [
            Envelope.from_dict(env)
            for env in envlist_dict
        ]

        return EnvelopeList(envlist)

    def write(self):
        raise NotImplementedError


