import os
from typing import List, Any

from pathlib import Path


def validate_points(role: str, p:int):
    if not isinstance(p, float):
        raise TypeError(f"invalid type for '{role}': expected 'float', got '{type(p)}' (value '{p}')")
    if p < 0 or p > 1:
        raise ValueError(f"invalid value for '{role}': should be between 0 and 1, got '{p}'")

# def validate_isfloat(i) -> None:
#     if not isinstance(i, float):
#         raise TypeError(f"invalid type: expected 'float', got '{type(i)}'")

# def validate_isint(i) -> None:
#     if not isinstance(i, int):
#         raise TypeError(f"invalid type: expected 'int', got '{type(i)}'")

# def validate_isbool(i) -> None:
#     if not isinstance(i, bool):
#         raise TypeError(f"invalid type: expected 'bool', got '{type(i)}'")

def validate_type(i, type_) -> Any:
    """
    if `i` is not of type `type_`, try to cast it to that type. if that fails, raise
    """
    if not isinstance(i, type_):
        try:
            i = type(i)
        except TypeError:
            raise TypeError(f"invalid type: expected '{type_}', got '{type(i)}' (and could not cast to type {type_})")
    return i

def validate_isinlist(i, vallist: List) -> None:
    if i not in vallist:
        raise ValueError(f"invalid value: expected one of {vallist}, got '{i}'")

def validate_iseq(a, b):
    if not a == b:
        raise ValueError(f"expected a==b (a={a}, b={b})")

def validate_islt(a, b):
    if not a < b:
        raise ValueError(f"expected a<b (a={a}, b={b})")

def validate_isle(a, b):
    if not a <= b:
        raise ValueError(f"expected a<=b (a={a}, b={b})")

def validate_isgt(a, b):
    if not a > b:
        raise ValueError(f"expected a>b (a={a}, b={b})")

def validate_isge(a, b):
    if not a >= b:
        raise ValueError(f"expected a>=b (a={a}, b={b})")

def validate_isinrange(
    i: float|int,
    min_: float|int,
    max_: float|int,
    inclusive: bool=False
) -> None:
    expr = (
       i < min_ or i > max_
       if not inclusive
       else i <= min_ or i >= max_
    )
    if expr:
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