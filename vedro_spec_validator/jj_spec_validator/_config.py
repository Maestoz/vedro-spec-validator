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
