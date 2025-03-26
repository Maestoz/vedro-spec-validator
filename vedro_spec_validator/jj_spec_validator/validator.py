from json import JSONDecodeError, loads
from typing import Any, TypeVar

from schemax import SchemaData
from d42.validation import ValidationException, validate_or_fail

from ._config import Config
from .utils import (create_openapi_matcher, get_forced_strict_spec, load_cache,
                    validate_non_strict)
from .validator_base import BaseValidator

_T = TypeVar('_T')

class Validator(BaseValidator):

    def __init__(self,
                 skip_if_failed_to_get_spec: bool,
                 is_raise_error: bool,
                 is_strict: bool,
                 func_name: str,
                 spec_link: str | None = None,
                 force_strict: bool = False,
                 prefix: str | None = None,
                 ):
        self.skip_if_failed_to_get_spec = skip_if_failed_to_get_spec
        self.is_raise_error = is_raise_error
        self.is_strict = is_strict
        self.func_name = func_name
        self.spec_link = spec_link
        self.force_strict = force_strict
        self.prefix = prefix

    @property
    def func_name(self) -> str:
        return self._func_name

    @func_name.setter
    def func_name(self, value: str) -> None:
        self._func_name = value

    @property
    def spec_link(self) -> str | None:
        return self._spec_link

    @spec_link.setter
    def spec_link(self, value: str | None) -> None:
        self._spec_link = value

    @property
    def skip_if_failed_to_get_spec(self) -> bool:
        return self._skip_if_failed_to_get_spec

    @skip_if_failed_to_get_spec.setter
    def skip_if_failed_to_get_spec(self, value: bool) -> None:
        self._skip_if_failed_to_get_spec = value

    def output(self,
               e: Exception,
               text: str = None,
               ) -> None:
        if Config.OUTPUT_FUNCTION is None:
            if text:
                print(f"⚠️ ⚠️ ⚠️ {text} in {self.func_name} :\n{str(e)}\n")
            else:
                print(f"⚠️ ⚠️ ⚠️ There are some mismatches in {self.func_name} :\n{str(e)}\n")
        else:
            Config.OUTPUT_FUNCTION(self.func_name, e, text)

    def _validation_failure(self,
                            exception: Exception,
                            ) -> None:
        self.output(exception)
        if self.is_raise_error:
            raise ValidationException(f"There are some mismatches in {self.func_name}:\n{str(exception)}")

    def prepare_data(self) -> dict[tuple[str, str, str], SchemaData] | None:
        if self.spec_link is None:
            raise ValueError("Spec link cannot be None")
        return load_cache(self)

    def _prepare_validation(self, mocked,
                           ) -> tuple[SchemaData | None, Any] | tuple[None, None]:
        mock_matcher = mocked.handler.matcher
        if mocked.handler.response.content_type.lower().startswith("application/json"):
            try:
                mocked_body = loads(mocked.handler.response.get_body())
            except JSONDecodeError:
                raise AssertionError(f"There is no valid JSON in {self.func_name}")
        else:
            mocked_body = mocked.handler.response.text

        spec_matcher = create_openapi_matcher(matcher=mock_matcher, prefix=self.prefix)

        if not spec_matcher:
            raise AssertionError(f"There is no valid matcher in {self.func_name}")

        prepared_spec = self.prepare_data()
        if prepared_spec is None:
            return None, None

        all_spec_units = prepared_spec.keys()
        formatted_units = "\n".join([str(key) for key in all_spec_units])

        matched_spec_units = [(http_method, path, status) for http_method, path, status in all_spec_units if
                              spec_matcher.match((http_method, path))]

        matched_status_spec_units = [(http_method, path, status) for http_method, path, status in matched_spec_units if
                                     status == mocked.handler.response.status]

        if len(matched_status_spec_units) > 1:
            raise AssertionError(f"There is more than 1 matches for mocked API method '{spec_matcher}\n"
                                 f"in the {self.spec_link}.")

        elif len(matched_status_spec_units) == 0:
            raise AssertionError(f"Mocked API method: {spec_matcher}, with status: {mocked.handler.response.status}\nwas not found in the {self.spec_link} "
                                 f"for the validation of {self.func_name}.\n"
                                 f"Presented units:\n{formatted_units}.")

        spec_unit = prepared_spec.get(matched_status_spec_units[0])

        return spec_unit, mocked_body

    def validate(self,
                 mocked: _T,
                 ) -> None:

        spec_unit, decoded_mocked_body = self._prepare_validation(mocked=mocked)
        if decoded_mocked_body is None:
            return None
        if spec_unit is not None:
            spec_response_schema = spec_unit.response_schema_d42
            if spec_response_schema:
                if self.force_strict:
                    spec_response_schema = get_forced_strict_spec(spec_response_schema)
                else:
                    spec_response_schema = spec_response_schema

                try:
                    if self.is_strict:
                        validate_or_fail(spec_response_schema, decoded_mocked_body)
                    else:
                        validate_non_strict(spec_response_schema, decoded_mocked_body)

                except ValidationException as exception:
                    self._validation_failure(exception)

        else:
            raise AssertionError(f"API method '{spec_unit}' in the spec_link"
                                 f" lacks a response structure for the validation of {self.func_name}")
