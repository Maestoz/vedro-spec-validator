import unittest
from unittest.mock import patch, Mock, MagicMock
import asyncio

from vedro_spec_validator.jj_spec_validator.validate_spec import validate_spec
from vedro_spec_validator.jj_spec_validator._config import Config
from vedro_spec_validator.jj_spec_validator.spec import Spec
from vedro_spec_validator.jj_spec_validator.validator import Validator


class TestValidateSpec(unittest.TestCase):
    def setUp(self):
        self.spec_link = "https://example.com/api/spec.json"
        self.original_is_enabled = Config.IS_ENABLED
        Config.IS_ENABLED = True
    
    def tearDown(self):
        Config.IS_ENABLED = self.original_is_enabled
    
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.output')
    def test_validate_spec_with_skip_reason(self, mock_output):
        skip_reason = "Test reason"
        
        @validate_spec(
            spec_link=self.spec_link,
            skip_reason=skip_reason
        )
        def test_func():
            return MagicMock()
        
        test_func()
        
        mock_output.assert_called_once()
        self.assertEqual(mock_output.call_args.kwargs['text'], f"test_func is skipped because: {skip_reason}")
    
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Spec')
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Validator')
    def test_validate_spec_initialization(self, mock_validator_class, mock_spec_class):
        mock_spec = Mock(spec=Spec)
        mock_spec_class.return_value = mock_spec
        
        mock_validator = Mock(spec=Validator)
        mock_validator_class.return_value = mock_validator
        
        @validate_spec(
            spec_link=self.spec_link,
            skip_if_failed_to_get_spec=True,
            is_raise_error=True,
            is_strict=True,
            prefix="/api",
            force_strict=True
        )
        def test_func():
            return MagicMock()
        
        test_func()
        
        mock_spec_class.assert_called_once_with(
            spec_link=self.spec_link,
            func_name="test_func",
            skip_if_failed_to_get_spec=True,
            is_strict=True,
            force_strict=True
        )
        
        mock_validator_class.assert_called_once_with(
            spec_link=self.spec_link,
            func_name="test_func",
            skip_if_failed_to_get_spec=True,
            is_raise_error=True,
            is_strict=True,
            prefix="/api",
            force_strict=True
        )
    
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Spec')
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Validator')
    def test_validate_spec_uses_config_defaults(self, mock_validator_class, mock_spec_class):
        mock_spec = Mock(spec=Spec)
        mock_spec_class.return_value = mock_spec
        
        mock_validator = Mock(spec=Validator)
        mock_validator_class.return_value = mock_validator
        
        original_skip = Config.SKIP_IF_FAILED_TO_GET_SPEC
        original_raises = Config.IS_RAISES
        original_strict = Config.IS_STRICT
        
        try:
            Config.SKIP_IF_FAILED_TO_GET_SPEC = True
            Config.IS_RAISES = True
            Config.IS_STRICT = True
            
            @validate_spec(spec_link=self.spec_link)
            def test_func():
                return MagicMock()
            
            test_func()
            
            mock_spec_class.assert_called_once_with(
                spec_link=self.spec_link,
                func_name="test_func",
                skip_if_failed_to_get_spec=True,
                is_strict=True,
                force_strict=False
            )
            
            mock_validator_class.assert_called_once_with(
                spec_link=self.spec_link,
                func_name="test_func",
                skip_if_failed_to_get_spec=True,
                is_raise_error=True,
                is_strict=True,
                prefix=None,
                force_strict=False
            )
            
        finally:
            Config.SKIP_IF_FAILED_TO_GET_SPEC = original_skip
            Config.IS_RAISES = original_raises
            Config.IS_STRICT = original_strict
    
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Spec')
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Validator')
    def test_validate_spec_sync_function(self, mock_validator_class, mock_spec_class):
        mock_spec = Mock(spec=Spec)
        mock_spec_class.return_value = mock_spec
        
        mock_validator = Mock(spec=Validator)
        mock_validator_class.return_value = mock_validator
        
        @validate_spec(spec_link=self.spec_link)
        def test_func(arg1, arg2=None):
            mock = MagicMock()
            mock.arg1 = arg1
            mock.arg2 = arg2
            return mock
        
        result = test_func("test", arg2="value")
        
        self.assertEqual(result.arg1, "test")
        self.assertEqual(result.arg2, "value")
        mock_validator.validate.assert_called_once_with(result, mock_spec)
    
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Spec')
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Validator')
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.isinstance')
    def test_validate_spec_relay_response(self, mock_isinstance, mock_validator_class, mock_spec_class):
        mock_spec = Mock(spec=Spec)
        mock_spec_class.return_value = mock_spec
        
        mock_validator = Mock(spec=Validator)
        mock_validator_class.return_value = mock_validator
        
        # Mock isinstance to correctly identify RelayResponse
        def isinstance_side_effect(obj, class_type):
            from vedro_spec_validator.jj_spec_validator.validate_spec import RelayResponse
            if class_type == RelayResponse:
                return True
            # For all other checks, call the real isinstance
            return isinstance(obj, class_type)
            
        mock_isinstance.side_effect = isinstance_side_effect
        
        @validate_spec(spec_link=self.spec_link)
        def test_func():
            mock = MagicMock()
            mock.handler.response = Mock()
            return mock
        
        with patch('builtins.print') as mock_print:
            result = test_func()
            
            mock_print.assert_called_once_with("RelayResponse type is not supported")
            mock_validator.validate.assert_not_called()
    
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Spec')
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Validator')
    def test_validate_spec_disabled(self, mock_validator_class, mock_spec_class):
        mock_spec = Mock(spec=Spec)
        mock_spec_class.return_value = mock_spec
        
        mock_validator = Mock(spec=Validator)
        mock_validator_class.return_value = mock_validator
        
        Config.IS_ENABLED = False
        
        @validate_spec(spec_link=self.spec_link)
        def test_func():
            return MagicMock()
        
        result = test_func()
        
        mock_validator.validate.assert_not_called()
    
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Spec')
    @patch('vedro_spec_validator.jj_spec_validator.validate_spec.Validator')
    def test_validate_spec_async_function(self, mock_validator_class, mock_spec_class):
        mock_spec = Mock(spec=Spec)
        mock_spec_class.return_value = mock_spec
        
        mock_validator = Mock(spec=Validator)
        mock_validator_class.return_value = mock_validator
        
        @validate_spec(spec_link=self.spec_link)
        async def test_func(arg1, arg2=None):
            mock = MagicMock()
            mock.arg1 = arg1
            mock.arg2 = arg2
            return mock
        
        async def run_test():
            result = await test_func("test", arg2="value")
            self.assertEqual(result.arg1, "test")
            self.assertEqual(result.arg2, "value")
            mock_validator.validate.assert_called_once_with(result, mock_spec)
        
        asyncio.run(run_test())


class TestValidateSpecAsyncDetection(unittest.TestCase):
    def test_is_coroutine_function_detection(self):
        async def async_func():
            pass
            
        def sync_func():
            pass
            
        self.assertTrue(asyncio.iscoroutinefunction(async_func))
        self.assertFalse(asyncio.iscoroutinefunction(sync_func)) 
        