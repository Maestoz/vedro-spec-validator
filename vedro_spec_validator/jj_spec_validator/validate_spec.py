import asyncio
import time
from functools import wraps
from typing import Callable, TypeVar

from jj import RelayResponse

from ._config import Config
from .output import output
from .spec import Spec, SchemaParseError
from .validator import Validator

_T = TypeVar('_T')


def validate_spec(*,
                  spec_link: str,
                  skip_reason: str | None = None,
                  skip_if_failed_to_get_spec: bool | None = None,
                  is_raise_error: bool | None = None,
                  is_strict: bool | None = None,
                  prefix: str | None = None,
                  force_strict: bool = False,
                  ) -> Callable[[Callable[..., _T]], Callable[..., _T]]:
    """
    Validates the jj mock function with given specification lint.

    Args:
       spec_link: The link to the specification.
       skip_if_failed_to_get_spec: If True - skip validation if failed to get spec. False is default.
       skip_reason: The reason to skip validation. If not None - skip validation.
       is_raise_error: If True - raises error when validation is failes. False is default.
       is_strict: If True - validate exact structure in given mocked.
       prefix: Prefix is used to cut paths prefix in mock function.
       force_strict: If True - forced remove all Ellipsis from the spec.
    """
    def decorator(func: Callable[..., _T]) -> Callable[..., _T]:
        func_name = func.__name__

        if skip_reason:
            output(text=f"{func_name} is skipped because: {skip_reason}")
        else:
            spec = Spec(
                spec_link=spec_link,
                func_name=func_name,
                skip_if_failed_to_get_spec=skip_if_failed_to_get_spec if skip_if_failed_to_get_spec is not None else Config.SKIP_IF_FAILED_TO_GET_SPEC,
                is_strict=is_strict if is_strict is not None else Config.IS_STRICT,
                force_strict=force_strict
            )

            validator = Validator(
                spec_link=spec_link,
                prefix=prefix,
                func_name=func_name,
                force_strict=force_strict,
                skip_if_failed_to_get_spec=skip_if_failed_to_get_spec if skip_if_failed_to_get_spec is not None else Config.SKIP_IF_FAILED_TO_GET_SPEC,
                is_raise_error=is_raise_error if is_raise_error is not None else Config.IS_RAISES,
                is_strict=is_strict if is_strict is not None else Config.IS_STRICT
                )

        @wraps(func)
        async def async_wrapper(*args: object, **kwargs: object) -> _T:
            mocked = await func(*args, **kwargs)
            if Config.IS_ENABLED and (not skip_reason):
                if isinstance(mocked.handler.response, RelayResponse):
                    print("RelayResponse type is not supported")
                    return mocked
                
                start_validate_time = time.perf_counter() if Config.SHOW_PERFORMANCE_METRICS else None
                validator.validate(mocked, spec)
                
                if Config.SHOW_PERFORMANCE_METRICS and start_validate_time is not None:
                    validate_time = time.perf_counter() - start_validate_time
                    print(f"🕒 [{func_name}] Validation time: {validate_time:.4f} sec")
            else:...
            return mocked

        @wraps(func)
        def sync_wrapper(*args: object, **kwargs: object) -> _T:
            mocked = func(*args, **kwargs)
            if Config.IS_ENABLED and (not skip_reason):
                if isinstance(mocked.handler.response, RelayResponse):
                    print("RelayResponse type is not supported")
                    return mocked
                
                start_validate_time = time.perf_counter() if Config.SHOW_PERFORMANCE_METRICS else None
                validator.validate(mocked, spec)
                
                if Config.SHOW_PERFORMANCE_METRICS and start_validate_time is not None:
                    validate_time = time.perf_counter() - start_validate_time
                    print(f"🕒 [{func_name}] Validation time: {validate_time:.4f} sec")
            else:...
            return mocked

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator
