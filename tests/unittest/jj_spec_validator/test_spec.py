import unittest
from unittest.mock import patch, Mock, mock_open, MagicMock, ANY
import httpx
import json
import yaml
from pathlib import Path

from vedro_spec_validator.jj_spec_validator.spec import Spec, SchemaParseError
from vedro_spec_validator.jj_spec_validator._config import Config
from schemax import SchemaData


class TestDownloadSpec(unittest.TestCase):
    def setUp(self):
        self.spec_link = "https://example.com/api/spec.json"
        self.func_name = "test_func"
        
    @patch('httpx.get')
    def test_download_spec_success(self, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        spec = Spec(self.spec_link, self.func_name)
        result = spec._download_spec()
        
        self.assertEqual(result, mock_response)
        mock_get.assert_called_once_with(self.spec_link, timeout=Config.GET_SPEC_TIMEOUT)
        mock_response.raise_for_status.assert_called_once()
    
    @patch('httpx.get')
    @patch('vedro_spec_validator.jj_spec_validator.spec.output')
    def test_download_spec_connect_timeout_skip(self, mock_output, mock_get):
        error_message = "Connection timeout"
        mock_get.side_effect = httpx.ConnectTimeout(error_message)
        
        spec = Spec(self.spec_link, self.func_name, skip_if_failed_to_get_spec=True)
        result = spec._download_spec()
        
        self.assertIsNone(result)
        mock_output.assert_called_once()
        self.assertEqual(mock_output.call_args.kwargs['func_name'], self.func_name)
        self.assertIsInstance(mock_output.call_args.kwargs['e'], httpx.ConnectTimeout)
        self.assertTrue(f"Timeout occurred while trying to connect to the {self.spec_link}" in mock_output.call_args.kwargs['text'])
    
    @patch('httpx.get')
    def test_download_spec_connect_timeout_raise(self, mock_get):
        error_message = "Connection timeout"
        original_exception = httpx.ConnectTimeout(error_message)
        mock_get.side_effect = original_exception
        
        spec = Spec(self.spec_link, self.func_name, skip_if_failed_to_get_spec=False)
        with self.assertRaises(httpx.ConnectTimeout) as context:
            spec._download_spec()
            
        self.assertTrue(f"Timeout occurred while trying to connect to the {self.spec_link}" in str(context.exception))
    
    @patch('httpx.get')
    @patch('vedro_spec_validator.jj_spec_validator.spec.output')
    def test_download_spec_read_timeout_skip(self, mock_output, mock_get):
        error_message = "Read timeout"
        mock_get.side_effect = httpx.ReadTimeout(error_message)
        
        spec = Spec(self.spec_link, self.func_name, skip_if_failed_to_get_spec=True)
        result = spec._download_spec()
        
        self.assertIsNone(result)
        mock_output.assert_called_once()
        self.assertEqual(mock_output.call_args.kwargs['func_name'], self.func_name)
        self.assertIsInstance(mock_output.call_args.kwargs['e'], httpx.ReadTimeout)
        self.assertTrue(f"Timeout occurred while trying to read the spec from the {self.spec_link}" in mock_output.call_args.kwargs['text'])
    
    @patch('httpx.get')
    def test_download_spec_read_timeout_raise(self, mock_get):
        error_message = "Read timeout"
        original_exception = httpx.ReadTimeout(error_message)
        mock_get.side_effect = original_exception
        
        spec = Spec(self.spec_link, self.func_name, skip_if_failed_to_get_spec=False)
        with self.assertRaises(httpx.ReadTimeout) as context:
            spec._download_spec()
            
        self.assertTrue(f"Timeout occurred while trying to read the spec from the {self.spec_link}" in str(context.exception))
    
    @patch('httpx.get')
    def test_download_spec_http_status_error_raise(self, mock_get):
        error_message = "404 Not Found"
        mock_request = Mock()
        mock_response = Mock()
        original_exception = httpx.HTTPStatusError(error_message, request=mock_request, response=mock_response)
        mock_get.side_effect = original_exception
        
        spec = Spec(self.spec_link, self.func_name, skip_if_failed_to_get_spec=False)
        with self.assertRaises(httpx.HTTPStatusError) as context:
            spec._download_spec()
        
        self.assertEqual(context.exception, original_exception)
    
    @patch('httpx.get')
    @patch('vedro_spec_validator.jj_spec_validator.spec.output')
    def test_download_spec_http_status_error_skip(self, mock_output, mock_get):
        error_message = "404 Not Found"
        mock_request = Mock()
        mock_response = Mock()
        original_exception = httpx.HTTPStatusError(error_message, request=mock_request, response=mock_response)
        mock_get.side_effect = original_exception
        
        spec = Spec(self.spec_link, self.func_name, skip_if_failed_to_get_spec=True)
        result = spec._download_spec()
        
        self.assertIsNone(result)
        mock_output.assert_called_once()
        self.assertEqual(mock_output.call_args.kwargs['func_name'], self.func_name)
        self.assertEqual(mock_output.call_args.kwargs['e'], original_exception)
    
    @patch('httpx.get')
    @patch('vedro_spec_validator.jj_spec_validator.spec.output')
    def test_download_spec_generic_http_error_skip(self, mock_output, mock_get):
        error_message = "HTTP Error"
        original_exception = httpx.HTTPError(error_message)
        mock_get.side_effect = original_exception
        
        spec = Spec(self.spec_link, self.func_name, skip_if_failed_to_get_spec=True)
        result = spec._download_spec()
        
        self.assertIsNone(result)
        mock_output.assert_called_once()
        self.assertEqual(mock_output.call_args.kwargs['func_name'], self.func_name)
        self.assertEqual(mock_output.call_args.kwargs['e'], original_exception)
        self.assertTrue(f"An HTTP error occurred while trying to download the {self.spec_link}" in mock_output.call_args.kwargs['text'])
    
    @patch('httpx.get')
    @patch('vedro_spec_validator.jj_spec_validator.spec.output')
    def test_download_spec_unexpected_error_skip(self, mock_output, mock_get):
        error_message = "Unexpected error"
        original_exception = Exception(error_message)
        mock_get.side_effect = original_exception
        
        spec = Spec(self.spec_link, self.func_name, skip_if_failed_to_get_spec=True)
        result = spec._download_spec()
        
        self.assertIsNone(result)
        mock_output.assert_called_once()
        self.assertEqual(mock_output.call_args.kwargs['func_name'], self.func_name)
        self.assertEqual(mock_output.call_args.kwargs['e'], original_exception)
        self.assertTrue(f"An unexpected error occurred while trying to download the {self.spec_link}" in mock_output.call_args.kwargs['text'])


class TestParseSpec(unittest.TestCase):
    def setUp(self):
        self.spec_link = "https://example.com/api/spec.json"
        self.func_name = "test_func"
        self.spec = Spec(self.spec_link, self.func_name)
    
    @patch('json.loads')
    def test_parse_spec_json_content_type(self, mock_loads):
        expected_result = {"key": "value"}
        mock_loads.return_value = expected_result
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_response.text = '{"key": "value"}'
        
        result = self.spec._parse_spec(mock_response)
        
        self.assertEqual(result, expected_result)
        mock_loads.assert_called_once_with(mock_response.text)
    
    @patch('yaml.load')
    def test_parse_spec_yaml_content_type(self, mock_yaml_load):
        expected_result = {"key": "value"}
        mock_yaml_load.return_value = expected_result
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/yaml"}
        mock_response.text = 'key: value'
        
        result = self.spec._parse_spec(mock_response)
        
        self.assertEqual(result, expected_result)
        mock_yaml_load.assert_called_once_with(mock_response.text, Loader=yaml.CLoader)
    
    @patch('yaml.load')
    def test_parse_spec_application_yaml_content_type(self, mock_yaml_load):
        expected_result = {"key": "value"}
        mock_yaml_load.return_value = expected_result
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "application/x-yaml"}
        mock_response.text = 'key: value'
        
        result = self.spec._parse_spec(mock_response)
        
        self.assertEqual(result, expected_result)
        mock_yaml_load.assert_called_once_with(mock_response.text, Loader=yaml.CLoader)
    
    @patch('json.loads')
    def test_parse_spec_json_file_extension(self, mock_loads):
        expected_result = {"key": "value"}
        mock_loads.return_value = expected_result
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = '{"key": "value"}'
        
        self.spec.spec_link = "https://example.com/api/specification.json"
        
        result = self.spec._parse_spec(mock_response)
        
        self.assertEqual(result, expected_result)
        mock_loads.assert_called_once_with(mock_response.text)
    
    @patch('yaml.load')
    def test_parse_spec_yaml_file_extension(self, mock_yaml_load):
        expected_result = {"key": "value"}
        mock_yaml_load.return_value = expected_result
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = 'key: value'
        
        self.spec.spec_link = "https://example.com/api/specification.yaml"
        
        result = self.spec._parse_spec(mock_response)
        
        self.assertEqual(result, expected_result)
        mock_yaml_load.assert_called_once_with(mock_response.text, Loader=yaml.CLoader)
    
    @patch('yaml.load')
    def test_parse_spec_yml_file_extension(self, mock_yaml_load):
        expected_result = {"key": "value"}
        mock_yaml_load.return_value = expected_result
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = 'key: value'
        
        self.spec.spec_link = "https://example.com/api/specification.yml"
        
        result = self.spec._parse_spec(mock_response)
        
        self.assertEqual(result, expected_result)
        mock_yaml_load.assert_called_once_with(mock_response.text, Loader=yaml.CLoader)
    
    def test_parse_spec_unsupported_content_type(self):
        mock_response = Mock()
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = 'some text'
        
        self.spec.spec_link = "https://example.com/api/spec.txt"
        
        with self.assertRaises(ValueError):
            self.spec._parse_spec(mock_response)


class TestGetSchemaFromJson(unittest.TestCase):
    def setUp(self):
        self.spec_link = "https://example.com/api/spec.json"
        self.func_name = "test_func"
        self.spec = Spec(self.spec_link, self.func_name)
    
    @patch('vedro_spec_validator.jj_spec_validator.spec.collect_schema_data')
    def test_get_schema_from_json_success(self, mock_collect_schema_data):
        raw_spec = {"paths": {"/test": {"get": {"responses": {"200": {}}}}}}
        expected_schema_data = [MagicMock(spec=SchemaData)]
        mock_collect_schema_data.return_value = expected_schema_data
        
        result = self.spec._get_schema_from_json(raw_spec)
        
        self.assertEqual(result, expected_schema_data)
        mock_collect_schema_data.assert_called_once_with(raw_spec)
    
    @patch('vedro_spec_validator.jj_spec_validator.spec.collect_schema_data')
    def test_get_schema_from_json_error(self, mock_collect_schema_data):
        raw_spec = {"invalid": "spec"}
        error_message = "Failed to parse schema"
        original_exception = Exception(error_message)
        mock_collect_schema_data.side_effect = original_exception
        
        with self.assertRaises(SchemaParseError) as context:
            self.spec._get_schema_from_json(raw_spec)
        
        self.assertTrue(f"Failed to parse {self.spec_link} to schema via schemax" in str(context.exception))
        self.assertTrue("Probably the spec is broken or has an unsupported format" in str(context.exception))
        self.assertTrue(f"Original exception: {original_exception}" in str(context.exception))
        
        mock_collect_schema_data.assert_called_once_with(raw_spec)


class TestBuildDictOfSchemas(unittest.TestCase):
    def setUp(self):
        self.spec_link = "https://example.com/api/spec.json"
        self.func_name = "test_func"
        self.spec = Spec(self.spec_link, self.func_name)
    
    def test_build_dict_of_schemas_success(self):
        mock_schema1 = Mock(spec=SchemaData)
        mock_schema1.http_method = "get"
        mock_schema1.path = "/test"
        mock_schema1.status = "200"
        
        mock_schema2 = Mock(spec=SchemaData)
        mock_schema2.http_method = "post"
        mock_schema2.path = "/test"
        mock_schema2.status = "201"
        
        schema_data = [mock_schema1, mock_schema2]
        
        result = self.spec._build_dict_of_schemas(schema_data)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[("GET", "/test", "200")], mock_schema1)
        self.assertEqual(result[("POST", "/test", "201")], mock_schema2)
    
    def test_build_dict_of_schemas_empty_list(self):
        schema_data = []
        
        with self.assertRaises(ValueError) as context:
            self.spec._build_dict_of_schemas(schema_data)
        self.assertEqual(str(context.exception), "Empty list of entities provided.")
    
    def test_build_dict_of_schemas_invalid_type(self):
        schema_data = [{"not": "a SchemaData object"}]
        
        with self.assertRaises(TypeError) as context:
            self.spec._build_dict_of_schemas(schema_data)
        self.assertTrue("Expected SchemaData, got" in str(context.exception))


class TestGetRawSpecFromFile(unittest.TestCase):
    def setUp(self):
        self.func_name = "test_func"
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"key": "value"}')
    @patch('json.loads')
    def test_get_raw_spec_from_file_json(self, mock_loads, mock_file, mock_exists):
        spec_link = "/path/to/spec.json"
        expected_result = {"key": "value"}
        mock_exists.return_value = True
        mock_loads.return_value = expected_result
        
        spec = Spec(spec_link, self.func_name)
        
        result = spec._get_raw_spec_from_file()
        
        self.assertEqual(result, expected_result)
        mock_exists.assert_called_once()
        mock_file.assert_called_once_with(ANY, 'r')
        self.assertEqual(mock_file.call_args.args[0], Path(spec_link))
        mock_loads.assert_called_once()
        self.assertEqual(mock_loads.call_args.args[0], '{"key": "value"}')
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='key: value')
    @patch('yaml.load')
    def test_get_raw_spec_from_file_yaml(self, mock_yaml_load, mock_file, mock_exists):
        spec_link = "/path/to/spec.yaml"
        expected_result = {"key": "value"}
        mock_exists.return_value = True
        mock_yaml_load.return_value = expected_result
        
        spec = Spec(spec_link, self.func_name)
        
        result = spec._get_raw_spec_from_file()
        
        self.assertEqual(result, expected_result)
        mock_exists.assert_called_once()
        mock_file.assert_called_once_with(ANY, 'r')
        self.assertEqual(mock_file.call_args.args[0], Path(spec_link))
        mock_yaml_load.assert_called_once()
        self.assertEqual(mock_yaml_load.call_args.args[0], 'key: value')
        self.assertEqual(mock_yaml_load.call_args.kwargs['Loader'], yaml.CLoader)
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='key: value')
    @patch('yaml.load')
    def test_get_raw_spec_from_file_yml(self, mock_yaml_load, mock_file, mock_exists):
        spec_link = "/path/to/spec.yml"
        expected_result = {"key": "value"}
        mock_exists.return_value = True
        mock_yaml_load.return_value = expected_result
        
        spec = Spec(spec_link, self.func_name)
        
        result = spec._get_raw_spec_from_file()
        
        self.assertEqual(result, expected_result)
        mock_exists.assert_called_once()
        mock_file.assert_called_once_with(ANY, 'r')
        self.assertEqual(mock_file.call_args.args[0], Path(spec_link))
        mock_yaml_load.assert_called_once()
        self.assertEqual(mock_yaml_load.call_args.args[0], 'key: value')
        self.assertEqual(mock_yaml_load.call_args.kwargs['Loader'], yaml.CLoader)
    
    @patch('pathlib.Path.exists')
    def test_get_raw_spec_from_file_not_found(self, mock_exists):
        spec_link = "/path/to/spec.json"
        mock_exists.return_value = False
        
        spec = Spec(spec_link, self.func_name)
        
        with self.assertRaises(FileNotFoundError) as context:
            spec._get_raw_spec_from_file()
        self.assertTrue(f"Specification file not found: {spec_link}" in str(context.exception))
        
        mock_exists.assert_called_once()
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='data')
    def test_get_raw_spec_from_file_unsupported_format(self, mock_file, mock_exists):
        spec_link = "/path/to/spec.txt"
        mock_exists.return_value = True
        
        spec = Spec(spec_link, self.func_name)
        
        with self.assertRaises(ValueError) as context:
            spec._get_raw_spec_from_file()
        self.assertTrue(f"Unsupported file format: .txt" in str(context.exception))
        
        mock_exists.assert_called_once()
        mock_file.assert_called_once_with(ANY, 'r')
        self.assertEqual(mock_file.call_args.args[0], Path(spec_link))


class TestGetPreparedSpecUnits(unittest.TestCase):
    def setUp(self):
        self.func_name = "test_func"
    
    def test_spec_link_none(self):
        spec = Spec(None, self.func_name)  # type: ignore
        
        with self.assertRaises(ValueError) as context:
            spec.get_prepared_spec_units()
        self.assertEqual(str(context.exception), "Spec link cannot be None")
    
    @patch('vedro_spec_validator.jj_spec_validator.spec.urlparse')
    @patch('vedro_spec_validator.jj_spec_validator.spec.validate_cache_file')
    @patch('vedro_spec_validator.jj_spec_validator.spec.load_cache')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._get_schema_from_json')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._build_dict_of_schemas')
    def test_get_prepared_spec_units_url_with_cache(self, mock_build_dict, mock_get_schema, 
                                                   mock_load_cache, mock_validate_cache, mock_urlparse):
        spec_link = "https://example.com/api/spec.json"
        url_parts = Mock()
        url_parts.scheme = "https"
        url_parts.netloc = "example.com"
        mock_urlparse.return_value = url_parts
        
        mock_validate_cache.return_value = True
        raw_spec = {"paths": {}}
        mock_load_cache.return_value = raw_spec
        
        mock_schema = Mock(spec=SchemaData)
        mock_schema.http_method = "get"
        mock_schema.path = "/test"
        mock_schema.status = "200"
        
        schema_data = [mock_schema]
        mock_get_schema.return_value = schema_data
        
        expected_result = {("GET", "/test", "200"): mock_schema}
        mock_build_dict.return_value = expected_result
        
        spec = Spec(spec_link, self.func_name)
        
        result = spec.get_prepared_spec_units()
        
        self.assertEqual(result, expected_result)
        mock_urlparse.assert_called_with(spec_link)
        mock_validate_cache.assert_called_once_with(spec_link)
        mock_load_cache.assert_called_once_with(spec_link)
        mock_get_schema.assert_called_once_with(raw_spec)
        mock_build_dict.assert_called_once_with(schema_data)
    
    @patch('vedro_spec_validator.jj_spec_validator.spec.urlparse')
    @patch('vedro_spec_validator.jj_spec_validator.spec.validate_cache_file')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._download_spec')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._parse_spec')
    @patch('vedro_spec_validator.jj_spec_validator.spec.save_cache')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._get_schema_from_json')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._build_dict_of_schemas')
    def test_get_prepared_spec_units_url_without_cache(self, mock_build_dict, mock_get_schema, 
                                                      mock_save_cache, mock_parse_spec, 
                                                      mock_download_spec, mock_validate_cache, mock_urlparse):
        spec_link = "https://example.com/api/spec.json"
        url_parts = Mock()
        url_parts.scheme = "https"
        url_parts.netloc = "example.com"
        mock_urlparse.return_value = url_parts
        
        mock_validate_cache.return_value = False
        
        mock_response = Mock()
        mock_download_spec.return_value = mock_response
        
        raw_spec = {"paths": {}}
        mock_parse_spec.return_value = raw_spec
        
        mock_schema = Mock(spec=SchemaData)
        mock_schema.http_method = "get"
        mock_schema.path = "/test"
        mock_schema.status = "200"
        
        schema_data = [mock_schema]
        mock_get_schema.return_value = schema_data
        
        expected_result = {("GET", "/test", "200"): mock_schema}
        mock_build_dict.return_value = expected_result
        
        spec = Spec(spec_link, self.func_name)
        
        result = spec.get_prepared_spec_units()
        
        self.assertEqual(result, expected_result)
        mock_urlparse.assert_called_with(spec_link)
        mock_validate_cache.assert_called_once_with(spec_link)
        mock_download_spec.assert_called_once()
        mock_parse_spec.assert_called_once_with(mock_response)
        mock_save_cache.assert_called_once_with(spec_link=spec_link, raw_schema=raw_spec)
        mock_get_schema.assert_called_once_with(raw_spec)
        mock_build_dict.assert_called_once_with(schema_data)
    
    @patch('vedro_spec_validator.jj_spec_validator.spec.urlparse')
    @patch('vedro_spec_validator.jj_spec_validator.spec.validate_cache_file')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._download_spec')
    def test_get_prepared_spec_units_download_none(self, mock_download_spec, 
                                                 mock_validate_cache, mock_urlparse):
        spec_link = "https://example.com/api/spec.json"
        url_parts = Mock()
        url_parts.scheme = "https"
        url_parts.netloc = "example.com"
        mock_urlparse.return_value = url_parts
        
        mock_validate_cache.return_value = False
        mock_download_spec.return_value = None
        
        spec = Spec(spec_link, self.func_name)
        
        result = spec.get_prepared_spec_units()
        
        self.assertIsNone(result)
        mock_urlparse.assert_called_with(spec_link)
        mock_validate_cache.assert_called_once_with(spec_link)
        mock_download_spec.assert_called_once()
    
    @patch('vedro_spec_validator.jj_spec_validator.spec.urlparse')
    @patch('pathlib.Path.is_absolute')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._get_raw_spec_from_file')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._get_schema_from_json')
    @patch('vedro_spec_validator.jj_spec_validator.spec.Spec._build_dict_of_schemas')
    def test_get_prepared_spec_units_file_path(self, mock_build_dict, mock_get_schema, 
                                              mock_get_raw_spec, mock_is_absolute, mock_urlparse):
        spec_link = "/path/to/spec.json"
        url_parts = Mock()
        url_parts.scheme = ""
        url_parts.netloc = ""
        mock_urlparse.return_value = url_parts
        
        mock_is_absolute.return_value = True
        
        raw_spec = {"paths": {}}
        mock_get_raw_spec.return_value = raw_spec
        
        mock_schema = Mock(spec=SchemaData)
        mock_schema.http_method = "get"
        mock_schema.path = "/test"
        mock_schema.status = "200"
        
        schema_data = [mock_schema]
        mock_get_schema.return_value = schema_data
        
        expected_result = {("GET", "/test", "200"): mock_schema}
        mock_build_dict.return_value = expected_result
        
        spec = Spec(spec_link, self.func_name)
        
        result = spec.get_prepared_spec_units()
        
        self.assertEqual(result, expected_result)
        mock_urlparse.assert_called_with(spec_link)
        mock_is_absolute.assert_called_once()
        mock_get_raw_spec.assert_called_once()
        mock_get_schema.assert_called_once_with(raw_spec)
        mock_build_dict.assert_called_once_with(schema_data)
    
    @patch('vedro_spec_validator.jj_spec_validator.spec.urlparse')
    @patch('pathlib.Path.is_absolute')
    def test_get_prepared_spec_units_invalid_path(self, mock_is_absolute, mock_urlparse):
        spec_link = "invalid/path/spec.json"
        url_parts = Mock()
        url_parts.scheme = ""
        url_parts.netloc = ""
        mock_urlparse.return_value = url_parts
        
        mock_is_absolute.return_value = False
        
        spec = Spec(spec_link, self.func_name)
        
        with self.assertRaises(ValueError) as context:
            spec.get_prepared_spec_units()
        self.assertEqual(str(context.exception), f"{spec_link} is neither a valid URL nor a valid path")
        
        mock_urlparse.assert_called_with(spec_link)
        mock_is_absolute.assert_called_once()
        