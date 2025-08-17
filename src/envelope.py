from .utils.validate import validate_float_isinrange

def validate_points(role: str, p:int):
    if not isinstance(p, float):
        raise ValueError(f"invalid type for '{role}': expected 'float', got '{type(p)}' (value '{p}')")
    if p < 0 or p > 1:
        raise ValueError(f"invalid value for '{role}': should be between 0 and 1, got '{p}'")

class Envelope:

    curves_allowed = ["linear"]

    def __init__(self, a:float, d:float, s:float, curve: str = "linear"):
        for k,v in {"a (attack)": a, "d (decay)": d, "s (sustain)": s }.items():
            validate_float_isinrange(v, 0, 1, inclusive=True)
        if curve not in self.curves_allowed:
            raise NotImplementedError(f"invalid value for 'curve': expected one of {self.curves_allowed}, got '{curve}'")

        self.a = a
        self.d = d
        self.s = s
        self.curve = curve
