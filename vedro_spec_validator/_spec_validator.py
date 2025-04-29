from typing import Callable, TypeVar

from .jj_spec_validator import validate_spec as validate_spec_external

_T = TypeVar('_T')


def validate_spec(*,
                  spec_link: str | None,
                  skip_reason: str | None = None,
                  skip_if_failed_to_get_spec: bool | None = None,
                  is_raise_error: bool | None = None,
                  is_strict: bool | None = None,
                  prefix: str | None = None,
                  force_strict: bool = False
                  ) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    return validate_spec_external(spec_link=spec_link,
                                  skip_reason=skip_reason,
                                  skip_if_failed_to_get_spec=skip_if_failed_to_get_spec,
                                  is_raise_error=is_raise_error,
                                  is_strict=is_strict,
                                  prefix=prefix,
                                  force_strict=force_strict)
