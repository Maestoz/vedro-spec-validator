from typing import Callable, TypeVar

from jj_spec_validator import validate_spec as validate_spec_external

_T = TypeVar('_T')


def validate_spec(*args, **kwargs) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    return validate_spec_external(*args, **kwargs)
