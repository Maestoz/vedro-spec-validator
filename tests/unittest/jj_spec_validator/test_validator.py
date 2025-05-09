import unittest
from unittest.mock import patch, Mock, MagicMock

from json import JSONDecodeError
from d42.validation import ValidationException
from schemax import SchemaData

from vedro_spec_validator.jj_spec_validator.validator import Validator
from vedro_spec_validator.jj_spec_validator.spec import Spec


class TestValidationFailure(unittest.TestCase):
    def setUp(self):
        self.func_name = "test_func"
        self.validator = Validator(
            skip_if_failed_to_get_spec=False,
            is_raise_error=False,
            is_strict=True,
            func_name=self.func_name,
            spec_link="https://example.com/api/spec.json"
        )
    
    @patch('vedro_spec_validator.jj_spec_validator.validator.output')
    def test_validation_failure_not_raise(self, mock_output):
        exception = Exception("Test exception")
        
        self.validator._validation_failure(exception)
        
        mock_output.assert_called_once()
        self.assertEqual(mock_output.call_args.kwargs['func_name'], self.func_name)
        self.assertEqual(mock_output.call_args.kwargs['e'], exception)
        self.assertTrue(f"There are some mismatches in {self.func_name}" in mock_output.call_args.kwargs['text'])

    @patch('vedro_spec_validator.jj_spec_validator.validator.output')
    def test_validation_failure_raise(self, mock_output):
        exception = Exception("Test exception")
        self.validator.is_raise_error = True
        
        with self.assertRaises(ValidationException) as context:
            self.validator._validation_failure(exception)
        
        self.assertTrue(f"There are some mismatches in {self.func_name}" in str(context.exception))
        self.assertTrue(str(exception) in str(context.exception))
        mock_output.assert_called_once()


class TestPrepareValidation(unittest.TestCase):
    def setUp(self):
        self.func_name = "test_func"
        self.spec_link = "https://example.com/api/spec.json"
        self.validator = Validator(
            skip_if_failed_to_get_spec=False,
            is_raise_error=False,
            is_strict=True,
            func_name=self.func_name,
            spec_link=self.spec_link
        )
        
        self.mock_spec = Mock(spec=Spec)
        
        self.mock_handler = Mock()
        self.mock_response = Mock()
        self.mock_matcher = Mock()
        
        self.mock_handler.matcher = self.mock_matcher
        self.mock_handler.response = self.mock_response
        
        self.mocked = Mock()
        self.mocked.handler = self.mock_handler
    
    @patch('vedro_spec_validator.jj_spec_validator.validator.loads')
    @patch('vedro_spec_validator.jj_spec_validator.validator.create_openapi_matcher')
    def test_prepare_validation_json_content(self, mock_create_matcher, mock_loads):
        self.mock_response.content_type = "application/json"
        self.mock_response.get_body.return_value = '{"key": "value"}'
        
        mock_loads.return_value = {"key": "value"}
        
        mock_spec_matcher = Mock()
        mock_spec_matcher.match.side_effect = lambda x: x == ("GET", "/test")
        mock_create_matcher.return_value = mock_spec_matcher
        
        mock_schema_data = Mock(spec=SchemaData)
        
        prepared_spec = {("GET", "/test", "200"): mock_schema_data}
        self.mock_spec.get_prepared_spec_units.return_value = prepared_spec
        
        self.mock_response.status = "200"
        
        spec_unit, mocked_body = self.validator._prepare_validation(self.mocked, self.mock_spec)
        
        self.assertEqual(spec_unit, mock_schema_data)
        self.assertEqual(mocked_body, {"key": "value"})
        mock_loads.assert_called_once_with(self.mock_response.get_body.return_value)
        mock_create_matcher.assert_called_once_with(matcher=self.mock_matcher, prefix=None)
        mock_spec_matcher.match.assert_called_with(("GET", "/test"))
    
    @patch('vedro_spec_validator.jj_spec_validator.validator.create_openapi_matcher')
    def test_prepare_validation_text_content(self, mock_create_matcher):
        self.mock_response.content_type = "text/plain"
        self.mock_response.text = "some text content"
        
        mock_spec_matcher = Mock()
        mock_spec_matcher.match.side_effect = lambda x: x == ("GET", "/test")
        mock_create_matcher.return_value = mock_spec_matcher
        
        mock_schema_data = Mock(spec=SchemaData)
        
        prepared_spec = {("GET", "/test", "200"): mock_schema_data}
        self.mock_spec.get_prepared_spec_units.return_value = prepared_spec
        
        self.mock_response.status = "200"
        
        spec_unit, mocked_body = self.validator._prepare_validation(self.mocked, self.mock_spec)
        
        self.assertEqual(spec_unit, mock_schema_data)
        self.assertEqual(mocked_body, "some text content")
        mock_create_matcher.assert_called_once_with(matcher=self.mock_matcher, prefix=None)
        mock_spec_matcher.match.assert_called_with(("GET", "/test"))
    
    @patch('vedro_spec_validator.jj_spec_validator.validator.loads')
    def test_prepare_validation_invalid_json(self, mock_loads):
        self.mock_response.content_type = "application/json"
        self.mock_response.get_body.return_value = 'invalid json'
        
        mock_loads.side_effect = JSONDecodeError("Invalid JSON", "invalid json", 0)
        
        with self.assertRaises(AssertionError) as context:
            self.validator._prepare_validation(self.mocked, self.mock_spec)
        
        self.assertTrue(f"There is no valid JSON in {self.func_name}" in str(context.exception))
    
    @patch('vedro_spec_validator.jj_spec_validator.validator.create_openapi_matcher')
    def test_prepare_validation_no_valid_matcher(self, mock_create_matcher):
        self.mock_response.content_type = "text/plain"
        self.mock_response.text = "some text content"
        
        mock_create_matcher.return_value = None
        
        with self.assertRaises(AssertionError) as context:
            self.validator._prepare_validation(self.mocked, self.mock_spec)
        
        self.assertTrue(f"There is no valid matcher in {self.func_name}" in str(context.exception))
    
    @patch('vedro_spec_validator.jj_spec_validator.validator.create_openapi_matcher')
    def test_prepare_validation_no_spec_units(self, mock_create_matcher):
        self.mock_response.content_type = "text/plain"
        self.mock_response.text = "some text content"
        
        mock_spec_matcher = Mock()
        mock_create_matcher.return_value = mock_spec_matcher
        
        self.mock_spec.get_prepared_spec_units.return_value = None
        
        spec_unit, mocked_body = self.validator._prepare_validation(self.mocked, self.mock_spec)
        
        self.assertIsNone(spec_unit)
        self.assertIsNone(mocked_body)
    
    @patch('vedro_spec_validator.jj_spec_validator.validator.create_openapi_matcher')
    def test_prepare_validation_multiple_matches(self, mock_create_matcher):
        self.mock_response.content_type = "text/plain"
        self.mock_response.text = "some text content"
        self.mock_response.status = "200"
        
        mock_spec_matcher = Mock()
        mock_spec_matcher.match.side_effect = lambda x: x[0] in ("GET", "POST")
        mock_create_matcher.return_value = mock_spec_matcher
        
        mock_schema_data1 = Mock(spec=SchemaData)
        mock_schema_data2 = Mock(spec=SchemaData)
        
        prepared_spec = {
            ("GET", "/test", "200"): mock_schema_data1,
            ("POST", "/other", "200"): mock_schema_data2
        }
        self.mock_spec.get_prepared_spec_units.return_value = prepared_spec
        
        with self.assertRaises(AssertionError) as context:
            self.validator._prepare_validation(self.mocked, self.mock_spec)
        
        self.assertTrue(f"There is more than 1 matches for mocked API method" in str(context.exception))
        mock_spec_matcher.match.assert_any_call(("GET", "/test"))
        mock_spec_matcher.match.assert_any_call(("POST", "/other"))
    
    @patch('vedro_spec_validator.jj_spec_validator.validator.create_openapi_matcher')
    def test_prepare_validation_no_status_match(self, mock_create_matcher):
        self.mock_response.content_type = "text/plain"
        self.mock_response.text = "some text content"
        self.mock_response.status = "404"
        
        mock_spec_matcher = Mock()
        mock_spec_matcher.match.side_effect = lambda x: x == ("GET", "/test")
        mock_create_matcher.return_value = mock_spec_matcher
        
        mock_schema_data = Mock(spec=SchemaData)
        
        prepared_spec = {("GET", "/test", "200"): mock_schema_data}
        self.mock_spec.get_prepared_spec_units.return_value = prepared_spec
        
        with self.assertRaises(AssertionError) as context:
            self.validator._prepare_validation(self.mocked, self.mock_spec)
        
        error_message = str(context.exception)
        self.assertTrue(f"Mocked API method: {mock_spec_matcher}, with status: 404" in error_message)
        self.assertTrue(f"was not found in the {self.spec_link}" in error_message)
        self.assertTrue("Presented units" in error_message)
        mock_spec_matcher.match.assert_called_with(("GET", "/test"))


class TestValidate(unittest.TestCase):
    def setUp(self):
        self.func_name = "test_func"
        self.spec_link = "https://example.com/api/spec.json"
        self.validator = Validator(
            skip_if_failed_to_get_spec=False,
            is_raise_error=False,
            is_strict=True,
            func_name=self.func_name,
            spec_link=self.spec_link
        )
        
        self.mock_spec = Mock(spec=Spec)
        self.mocked = Mock()
    
    @patch.object(Validator, '_prepare_validation')
    def test_validate_no_decoded_body(self, mock_prepare_validation):
        mock_prepare_validation.return_value = (None, None)
        
        result = self.validator.validate(self.mocked, self.mock_spec)
        
        self.assertIsNone(result)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
    
    @patch.object(Validator, '_prepare_validation')
    def test_validate_no_spec_unit(self, mock_prepare_validation):
        mock_prepare_validation.return_value = (None, {"key": "value"})
        
        with self.assertRaises(AssertionError) as context:
            self.validator.validate(self.mocked, self.mock_spec)
        
        error_message = str(context.exception)
        self.assertTrue(f"API method 'None' in the spec_link" in error_message)
        self.assertTrue(f"lacks a response structure for the validation of {self.func_name}" in error_message)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
    
    @patch.object(Validator, '_prepare_validation')
    @patch('vedro_spec_validator.jj_spec_validator.validator.has_ellipsis_in_all_branches')
    @patch('vedro_spec_validator.jj_spec_validator.validator.validate_or_fail')
    def test_validate_strict_validation(self, mock_validate_or_fail, mock_has_ellipsis, mock_prepare_validation):
        mock_schema_data = Mock(spec=SchemaData)
        mock_schema_data.response_schema_d42 = {"type": "object"}
        mock_prepare_validation.return_value = (mock_schema_data, {"key": "value"})
        mock_has_ellipsis.return_value = False
        
        result = self.validator.validate(self.mocked, self.mock_spec)
        
        self.assertIsNone(result)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
        mock_validate_or_fail.assert_called_once_with(mock_schema_data.response_schema_d42, {"key": "value"})
    
    @patch.object(Validator, '_prepare_validation')
    @patch('vedro_spec_validator.jj_spec_validator.validator.has_ellipsis_in_all_branches')
    @patch('vedro_spec_validator.jj_spec_validator.validator.validate_non_strict')
    def test_validate_non_strict_validation(self, mock_validate_non_strict, mock_has_ellipsis, mock_prepare_validation):
        self.validator.is_strict = False
        
        mock_schema_data = Mock(spec=SchemaData)
        mock_schema_data.response_schema_d42 = {"type": "object"}
        mock_prepare_validation.return_value = (mock_schema_data, {"key": "value"})
        mock_has_ellipsis.return_value = False
        
        result = self.validator.validate(self.mocked, self.mock_spec)
        
        self.assertIsNone(result)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
        mock_validate_non_strict.assert_called_once_with(mock_schema_data.response_schema_d42, {"key": "value"})
    
    @patch.object(Validator, '_prepare_validation')
    @patch('vedro_spec_validator.jj_spec_validator.validator.has_ellipsis_in_all_branches')
    @patch('vedro_spec_validator.jj_spec_validator.validator.validate_or_fail')
    @patch('vedro_spec_validator.jj_spec_validator.validator.output')
    def test_validate_with_ellipsis_warning(self, mock_output, mock_validate_or_fail, mock_has_ellipsis, mock_prepare_validation):
        mock_schema_data = Mock(spec=SchemaData)
        mock_schema_data.response_schema_d42 = {"type": "object"}
        mock_prepare_validation.return_value = (mock_schema_data, {"key": "value"})
        mock_has_ellipsis.return_value = True
        
        result = self.validator.validate(self.mocked, self.mock_spec)
        
        self.assertIsNone(result)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
        mock_output.assert_called_once()
        self.assertTrue("`force_strict=True` is required" in mock_output.call_args.kwargs['text'])
    
    @patch.object(Validator, '_prepare_validation')
    @patch('vedro_spec_validator.jj_spec_validator.validator.has_ellipsis_in_all_branches')
    @patch('vedro_spec_validator.jj_spec_validator.validator.get_forced_strict_spec')
    @patch('vedro_spec_validator.jj_spec_validator.validator.validate_or_fail')
    def test_validate_force_strict(self, mock_validate_or_fail, mock_get_forced, mock_has_ellipsis, mock_prepare_validation):
        self.validator.force_strict = True
        
        mock_schema_data = Mock(spec=SchemaData)
        mock_schema_data.response_schema_d42 = {"type": "object"}
        mock_prepare_validation.return_value = (mock_schema_data, {"key": "value"})
        mock_has_ellipsis.return_value = True
        mock_get_forced.return_value = {"type": "object", "strict": True}
        
        result = self.validator.validate(self.mocked, self.mock_spec)
        
        self.assertIsNone(result)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
        mock_get_forced.assert_called_once_with(mock_schema_data.response_schema_d42)
        mock_validate_or_fail.assert_called_once_with({"type": "object", "strict": True}, {"key": "value"})
    
    @patch.object(Validator, '_prepare_validation')
    @patch('vedro_spec_validator.jj_spec_validator.validator.has_ellipsis_in_all_branches')
    @patch('vedro_spec_validator.jj_spec_validator.validator.get_forced_strict_spec')
    @patch('vedro_spec_validator.jj_spec_validator.validator.validate_or_fail')
    @patch('vedro_spec_validator.jj_spec_validator.validator.output')
    def test_validate_unnecessary_force_strict(self, mock_output, mock_validate_or_fail, mock_get_forced, mock_has_ellipsis, mock_prepare_validation):
        self.validator.force_strict = True
        
        mock_schema_data = Mock(spec=SchemaData)
        mock_schema_data.response_schema_d42 = {"type": "object"}
        mock_prepare_validation.return_value = (mock_schema_data, {"key": "value"})
        mock_has_ellipsis.return_value = False
        mock_get_forced.return_value = {"type": "object", "strict": True}
        
        result = self.validator.validate(self.mocked, self.mock_spec)
        
        self.assertIsNone(result)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
        mock_output.assert_called_once()
        self.assertTrue("`force_strict=True` is not required" in mock_output.call_args.kwargs['text'])
    
    @patch.object(Validator, '_prepare_validation')
    @patch('vedro_spec_validator.jj_spec_validator.validator.has_ellipsis_in_all_branches')
    @patch('vedro_spec_validator.jj_spec_validator.validator.validate_or_fail')
    @patch.object(Validator, '_validation_failure')
    def test_validate_validation_exception(self, mock_validation_failure, mock_validate_or_fail, mock_has_ellipsis, mock_prepare_validation):
        mock_schema_data = Mock(spec=SchemaData)
        mock_schema_data.response_schema_d42 = {"type": "object"}
        mock_prepare_validation.return_value = (mock_schema_data, {"key": "value"})
        mock_has_ellipsis.return_value = False
        
        exception = ValidationException("Validation error")
        mock_validate_or_fail.side_effect = exception
        
        result = self.validator.validate(self.mocked, self.mock_spec)
        
        self.assertIsNone(result)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
        mock_validation_failure.assert_called_once_with(exception)
        mock_validate_or_fail.assert_called_once_with(mock_schema_data.response_schema_d42, {"key": "value"})
    
    @patch.object(Validator, '_prepare_validation')
    def test_validate_no_response_schema(self, mock_prepare_validation):
        mock_schema_data = Mock(spec=SchemaData)
        mock_schema_data.response_schema_d42 = None
        mock_prepare_validation.return_value = (mock_schema_data, {"key": "value"})
        
        result = self.validator.validate(self.mocked, self.mock_spec)
        
        self.assertIsNone(result)
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
        self.assertTrue(hasattr(mock_schema_data, 'response_schema_d42'))
    
    @patch.object(Validator, '_prepare_validation')
    @patch.object(Validator, '_validation_failure')
    def test_validate_decoded_body_without_spec_unit(self, mock_validation_failure, mock_prepare_validation):
        mock_body = {"key": "value"}
        mock_prepare_validation.return_value = (None, mock_body)
        
        with self.assertRaises(AssertionError) as context:
            self.validator.validate(self.mocked, self.mock_spec)
        
        error_message = str(context.exception)
        self.assertTrue(f"API method 'None' in the spec_link" in error_message)
        self.assertTrue(f"lacks a response structure for the validation of {self.func_name}" in error_message)
        
        mock_prepare_validation.assert_called_once_with(mocked=self.mocked, spec=self.mock_spec)
        mock_validation_failure.assert_not_called()
