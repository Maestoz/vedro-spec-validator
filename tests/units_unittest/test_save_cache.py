import unittest
from unittest.mock import patch, mock_open, Mock

from vedro_spec_validator.jj_spec_validator.utils._cacheir import save_cache, CACHE_DIR

class TestSaveCache(unittest.TestCase):
    @patch("vedro_spec_validator.jj_spec_validator.utils._cacheir.dump")
    @patch("vedro_spec_validator.jj_spec_validator.utils._cacheir.open", new_callable=mock_open)
    @patch("vedro_spec_validator.jj_spec_validator.utils._cacheir.makedirs")
    @patch("vedro_spec_validator.jj_spec_validator.utils._cacheir._get_cache_filename")
    def test_save_cache(self, mock_get_filename, mock_makedirs, mock_open_fn, mock_dump):
        spec_link = "http://example.com/openapi.yaml"
        raw_schema = {"openapi": "3.0.0"}
        fake_filename = "/tmp/fake_cache_file.cache"

        mock_get_filename.return_value = fake_filename

        save_cache(spec_link, raw_schema)

        mock_get_filename.assert_called_once_with(spec_link)
        mock_makedirs.assert_called_once_with(CACHE_DIR, exist_ok=True)
        mock_open_fn.assert_called_once_with(fake_filename, 'wb')
        mock_dump.assert_called_once_with(raw_schema, mock_open_fn.return_value.__enter__.return_value)

    def test_should_fail_when_spec_link_is_empty(self):
        spec_link = ""
        raw_schema = {"openapi": "3.0.0"}

        with self.assertRaises(ValueError) as exc_info:
            save_cache(spec_link, raw_schema)

        self.assertIn("spec_link must be", str(exc_info.exception))

    @patch("vedro_spec_validator.jj_spec_validator.utils._cacheir.dump", side_effect=TypeError("Unserializable!"))
    @patch("vedro_spec_validator.jj_spec_validator.utils._cacheir.open", new_callable=mock_open)
    @patch("vedro_spec_validator.jj_spec_validator.utils._cacheir.makedirs")
    def test_should_fail_when_raw_schema_contains_unserializable_data(self, mock_makedirs, mock_open_fn, mock_dump):
        spec_link = "http://example.com/openapi.yaml"
        raw_schema = {"callback": lambda x: x}

        with self.assertRaises(TypeError) as exc_info:
            save_cache(spec_link, raw_schema)

        self.assertIn("Unserializable", str(exc_info.exception))

if __name__ == "__main__":
    unittest.main()