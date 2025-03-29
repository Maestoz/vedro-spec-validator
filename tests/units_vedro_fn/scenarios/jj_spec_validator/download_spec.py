from unittest.mock import Mock, patch

import httpx
from jj.mock import Mock
from vedro import params
from vedro_fn import given, scenario, then, when

from vedro_spec_validator.jj_spec_validator import Config
from vedro_spec_validator.jj_spec_validator.utils._cacheir import _download_spec
from vedro_spec_validator.jj_spec_validator.validator import Validator


def get_random_validator(skip_if_failed_to_get_spec: bool) -> Validator:
    """Generate a random Validator instance with a random spec link."""
    spec_link = f"http://example.com/spec.yaml"
    return Validator(
        spec_link=spec_link,
        skip_if_failed_to_get_spec=skip_if_failed_to_get_spec,
        func_name="random_func_name",
        is_raise_error=False,
        is_strict=False
    )


@scenario()
def download_spec_happy_path():
    with given:
        random_validator = get_random_validator(skip_if_failed_to_get_spec=False)
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

    with when:
        with patch("httpx.get", return_value=mock_response) as mock_get:
            result = _download_spec(random_validator)

    with then:
        assert result is mock_response
        mock_get.assert_called_once_with("http://example.com/spec.yaml", timeout=Config.GET_SPEC_TIMEOUT)

@scenario([
    params(404, "Client error", "Not Found"),
    params(500, "Server error", "Internal Server Error"),
])
def download_spec_handle_status_error_exception(status_code, error_message, reason_phrase):
    with given:
        random_validator = get_random_validator(skip_if_failed_to_get_spec=True)
        random_validator.output = Mock()
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.reason_phrase = reason_phrase

        error = httpx.HTTPStatusError(
            message=error_message,
            request=Mock(),
            response=mock_response
        )

        mock_response.raise_for_status.side_effect = error

    with when:
        with patch("httpx.get", return_value=mock_response) as mock_get:
            result = _download_spec(random_validator)

    with then:
        assert result is None
        exc_arg, msg_arg = random_validator.output.call_args[0]
        assert isinstance(exc_arg, httpx.HTTPStatusError)
        assert f"{error_message} occurred: {str(status_code)}" in msg_arg
        mock_get.assert_called_once_with("http://example.com/spec.yaml", timeout=Config.GET_SPEC_TIMEOUT)

@scenario([
    params(httpx.ConnectTimeout, "Timeout occurred while trying to connect to the"),
    params(httpx.ReadTimeout, "Timeout occurred while trying to read the spec from the")
])
def download_spec_handle_timeout_exception(timeout_exception, error_message):
    with given:
        random_validator = get_random_validator(skip_if_failed_to_get_spec=True)
        random_validator.output = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = timeout_exception("Timeout occurred")

    with when:
        with patch("httpx.get", return_value=mock_response) as mock_get:
            result = _download_spec(random_validator)

    with then:
        assert result is None
        exc_arg, msg_arg = random_validator.output.call_args[0]
        assert isinstance(exc_arg, timeout_exception)
        assert error_message in msg_arg
        mock_get.assert_called_once_with("http://example.com/spec.yaml", timeout=Config.GET_SPEC_TIMEOUT)

@scenario()
def download_spec_handle_http_error_exception():
    with given:
        random_validator = get_random_validator(skip_if_failed_to_get_spec=True)
        random_validator.output = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPError("HTTP error occurred")

    with when:
        with patch("httpx.get", return_value=mock_response) as mock_get:
            result = _download_spec(random_validator)

    with then:
        assert result is None
        exc_arg, msg_arg = random_validator.output.call_args[0]
        assert isinstance(exc_arg, httpx.HTTPError)
        assert "An HTTP error occurred while trying to download the" in msg_arg
        mock_get.assert_called_once_with("http://example.com/spec.yaml", timeout=Config.GET_SPEC_TIMEOUT)

@scenario()
def download_spec_skip_if_failed_false():
    with given:
        random_validator = get_random_validator(skip_if_failed_to_get_spec=False)
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception

    with when:
        with patch("httpx.get", return_value=mock_response):
            raised_exception = None
            try:
                result = _download_spec(random_validator)
            except Exception as e:
                raised_exception = e

    with then:
        assert raised_exception is not None
        assert isinstance(raised_exception, Exception)
        assert "An unexpected error occurred while trying to download the" in str(raised_exception)