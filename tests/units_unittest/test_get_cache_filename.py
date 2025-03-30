import unittest
from hashlib import md5
from os import path

from vedro_spec_validator.jj_spec_validator.utils._cacheir import _get_cache_filename
from vedro_spec_validator.jj_spec_validator.utils._cacheir import CACHE_DIR


class TestGetCacheFilename(unittest.TestCase):
    def test_should_return_expected_cache_path(self):
        url = "http://example.com/openapi.yaml"
        expected_hash = md5(url.encode()).hexdigest()
        expected_path = path.join(CACHE_DIR, expected_hash + ".cache")

        result = _get_cache_filename(url)

        self.assertEqual(result, expected_path)


if __name__ == "__main__":
    unittest.main()