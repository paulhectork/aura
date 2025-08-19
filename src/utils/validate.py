import operator
from pathlib import Path
from typing import List, Any, Literal

ALLOWED_OPS = ["eq","gt","ge","lt","le"]

def validate_points(role: str, p:int):
    if not isinstance(p, float):
        raise TypeError(f"invalid type for '{role}': expected 'float', got '{type(p)}' (value '{p}')")
    if p < 0 or p > 1:
        raise ValueError(f"invalid value for '{role}': should be between 0 and 1, got '{p}'")

def validate_type(i, type_) -> Any:
    """
    if `i` is not of type `type_`, try to cast it to that type. if that fails, raise
    """
    if not isinstance(i, type_):
        try:
            i = type_(i)
        except TypeError:
            raise TypeError(f"invalid type: expected '{type_}', got '{type(i)}' (and could not cast to type {type_})")
    return i

def validate_comparison(opname: Literal["eq","gt","ge","lt","le"], a:Any,b:Any) -> None:
    """general function to ensure that a and b validate a certain comparison (a<b...)"""
    if opname not in ALLOWED_OPS:
        raise ValueError(f"invalid value for 'op': '{opname}'. expected one of '{ALLOWED_OPS}'")
    op = {
        "gt": operator.gt,
        "ge": operator.ge,
        "eq": operator.eq,
        "lt": operator.lt,
        "le": operator.le,
    }[opname]
    if not op(a, b):
        raise ValueError(f"failed comparison: expected a<'{opname}'>b (a={a}, b={b})")

def validate_isinlist(i, vallist: List) -> None:
    if i not in vallist:
        raise ValueError(f"invalid value: expected one of {vallist}, got '{i}'")

def validate_isinrange(
    i: float|int,
    min_: float|int,
    max_: float|int,
    inclusive: bool=False
) -> None:
    valid = (
       (i <= min_ or i >= max_)
       if inclusive
       else (i < min_ or i > max_)
    )
    if not valid:
        raise ValueError(f"invalid value: should be in range ({min_},{max_}), got '{i}' (inclusive bounds: {inclusive})")

def validate_float_isinrange(
    i: float|int,
    min_: float|int,
    max_: float|int,
    inclusive: bool=False
) -> None:
    i = validate_type(i,float)
    validate_isinrange(i, min_, max_, inclusive)


def validate_path_exists(fp:Path):
    if not fp.exists():
        raise FileNotFoundError(f"input file '{fp}' not found")