from typing import Callable

from schemax import Memoizer


class Config:
    # service
    MAIN_DIRECTORY = "spec_validator"
    GET_SPEC_TIMEOUT = 30.0
    IS_ENABLED = True

    # interface
    OUTPUT_FUNCTION = None  # can be used for custom output func

    # params
    IS_RAISES = False
    IS_STRICT = False
    SKIP_IF_FAILED_TO_GET_SPEC = False
    SHOW_PERFORMANCE_METRICS = False  # if True, execution time metrics will be printed to console
    CACHE_AS_PROCESSED_SCHEMAS = False  # If True, converts specifications into schemas and caches them that way
    SKIP_VALIDATED_STRUCTURES: bool = False  # If True, skips validation for already validated response structures
    MEMOIZER_FACTORY: Callable[[], Memoizer] = lambda: None  # Provides memoization for plugin's inner workings
