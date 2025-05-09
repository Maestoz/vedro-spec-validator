from json import JSONDecodeError, loads
from typing import Any, TypeVar

from d42.validation import ValidationException, validate_or_fail
from schemax import SchemaData

from . import Config
from .output import output
from .spec import Spec
from .utils import create_openapi_matcher, get_forced_strict_spec, load_cache, validate_non_strict
from .utils._refiner import has_ellipsis_in_all_branches

_T = TypeVar('_T')

class Validator:

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

    def _validation_failure(self, exception: Exception) -> None:
        output(func_name=self.func_name, text=f"⚠️ ⚠️ ⚠️ There are some mismatches in {self.func_name} :", e=exception)

        if self.is_raise_error:
            raise ValidationException(f"There are some mismatches in {self.func_name}:\n{str(exception)}") from None

    def _prepare_validation(self, mocked, spec: Spec,
                           ) -> tuple[SchemaData | None, Any] | tuple[None, None]:

        if mocked.handler.response.content_type.lower().startswith("application/json"):
            try:
                mocked_body = loads(mocked.handler.response.get_body())
            except JSONDecodeError:
                raise AssertionError(f"There is no valid JSON in {self.func_name}")
        else:
            mocked_body = mocked.handler.response.text

        mock_matcher = mocked.handler.matcher
        spec_matcher = create_openapi_matcher(matcher=mock_matcher, prefix=self.prefix)

        if not spec_matcher:
            raise AssertionError(f"There is no valid matcher in {self.func_name}")

        prepared_spec = spec.get_prepared_spec_units()
        if prepared_spec is None:
            return None, None

        all_spec_units = prepared_spec.keys()

        matched_spec_units = [(http_method, path, status) for http_method, path, status in all_spec_units if
                              spec_matcher.match((http_method, path))]

        matched_status_spec_units = [(http_method, path, status) for http_method, path, status in matched_spec_units if
                                     status == mocked.handler.response.status]

        if len(matched_status_spec_units) > 1:
            raise AssertionError(f"There is more than 1 matches for mocked API method '{spec_matcher}\n"
                                 f"in the {self.spec_link}.")

        elif len(matched_status_spec_units) == 0:
            formatted_units = "\n".join([str(key) for key in all_spec_units])
            raise AssertionError(f"Mocked API method: {spec_matcher}, with status: {mocked.handler.response.status}\nwas not found in the {self.spec_link} "
                                 f"for the validation of {self.func_name}.\n"
                                 f"Presented units:\n{formatted_units}.")

        spec_unit = prepared_spec.get(matched_status_spec_units[0])

        return spec_unit, mocked_body

    def validate(self, mocked: _T, spec: Spec) -> None:

        spec_unit, decoded_mocked_body = self._prepare_validation(mocked=mocked, spec=spec)
        if decoded_mocked_body is None:
            return None
        if spec_unit is not None:
            spec_response_schema = spec_unit.response_schema_d42
            if spec_response_schema:
                if self.force_strict:
                    if not has_ellipsis_in_all_branches(spec_response_schema):
                        output(func_name=self.func_name, text=f"⚠️ ⚠️ ⚠️ `force_strict=True` is not required for {self.func_name}!\n")
                    spec_response_schema = get_forced_strict_spec(spec_response_schema)
                else:
                    if has_ellipsis_in_all_branches(spec_response_schema):
                        output(func_name=self.func_name, text=f"⚠️ Probably `force_strict=True` is required for {self.func_name}.\n")
                    spec_response_schema = spec_response_schema

                try:
                    if self.is_strict:
                        validate_or_fail(spec_response_schema, decoded_mocked_body)
                    else:
                        validate_non_strict(spec_response_schema, decoded_mocked_body)

                except ValidationException as exception:
                    self._validation_failure(exception)
            return None

        else:
            raise AssertionError(f"API method '{spec_unit}' in the spec_link"
                                 f" lacks a response structure for the validation of {self.func_name}")
