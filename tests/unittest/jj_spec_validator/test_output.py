import unittest
from unittest.mock import patch, Mock, call
import sys
from io import StringIO

from vedro_spec_validator.jj_spec_validator.output import output
from vedro_spec_validator.jj_spec_validator._config import Config


class TestOutput(unittest.TestCase):
    def setUp(self):
        self.original_stdout = sys.stdout
        self.stdout_mock = StringIO()
        sys.stdout = self.stdout_mock
        
        self.original_output_function = Config.OUTPUT_FUNCTION
    
    def tearDown(self):
        sys.stdout = self.original_stdout
        
        Config.OUTPUT_FUNCTION = self.original_output_function
    
    def test_output_with_text_and_exception(self):
        Config.OUTPUT_FUNCTION = None
        func_name = "test_func"
        text = "Error message"
        exception = Exception("Test exception")
        
        output(func_name=func_name, text=text, e=exception)
        
        output_content = self.stdout_mock.getvalue()
        self.assertIn(text, output_content)
        self.assertIn(f"Exception: {str(exception)}", output_content)
    
    def test_output_with_exception_only(self):
        Config.OUTPUT_FUNCTION = None
        func_name = "test_func"
        exception = Exception("Test exception")
        
        output(func_name=func_name, e=exception)
        
        output_content = self.stdout_mock.getvalue()
        self.assertIn(f"Exception: {str(exception)}", output_content)
        self.assertNotIn("None", output_content)
    
    def test_output_with_text_only(self):
        Config.OUTPUT_FUNCTION = None
        func_name = "test_func"
        text = "Info message"
        
        output(func_name=func_name, text=text)
        
        output_content = self.stdout_mock.getvalue()
        self.assertIn(text, output_content)
        self.assertNotIn("Exception", output_content)
    
    def test_output_with_custom_function(self):
        mock_output_function = Mock()
        Config.OUTPUT_FUNCTION = mock_output_function
        
        func_name = "test_func"
        text = "Custom message"
        exception = Exception("Custom exception")
        
        output(func_name=func_name, text=text, e=exception)
        
        mock_output_function.assert_called_once_with(func_name, text, exception)
        
        output_content = self.stdout_mock.getvalue()
        self.assertEqual("", output_content)
    
    def test_output_with_empty_inputs(self):
        Config.OUTPUT_FUNCTION = None
        
        output()
        
        output_content = self.stdout_mock.getvalue()
        self.assertIn("None\n", output_content)
    
    def test_output_with_func_name_only(self):
        Config.OUTPUT_FUNCTION = None
        func_name = "test_func"
        
        output(func_name=func_name)
        
        output_content = self.stdout_mock.getvalue()
        self.assertIn("None\n", output_content)
        self.assertNotIn(func_name, output_content)
    
    @patch('builtins.print')
    def test_output_print_called_correctly(self, mock_print):
        Config.OUTPUT_FUNCTION = None
        func_name = "test_func"
        text = "Message"
        exception = Exception("Test exception")
        
        output(func_name=func_name, text=text, e=exception)
        output(func_name=func_name, text=text)
        output(func_name=func_name, e=exception)
        
        self.assertEqual(mock_print.call_count, 3)
        mock_print.assert_has_calls([
            call(f"{text}\nException: {str(exception)}\n"),
            call(f"{text}\n"),
            call(f"\nException: {str(exception)}\n")
        ]) 