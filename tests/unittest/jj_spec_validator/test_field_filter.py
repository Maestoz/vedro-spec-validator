import unittest

from vedro_spec_validator.jj_spec_validator.utils._field_filter import (
    filter_ignored_fields,
    parse_ignore_patterns,
    should_ignore_field,
)


class TestParseIgnorePatterns(unittest.TestCase):
    """Tests for parse_ignore_patterns function."""

    def test_empty_string_returns_empty_list(self):
        result = parse_ignore_patterns("")
        self.assertEqual(result, [])

    def test_single_pattern(self):
        result = parse_ignore_patterns("x-*")
        self.assertEqual(result, ["x-*"])

    def test_multiple_patterns(self):
        result = parse_ignore_patterns("x-*,name[*],test-*")
        self.assertEqual(result, ["x-*", "name[*]", "test-*"])

    def test_patterns_with_spaces(self):
        result = parse_ignore_patterns("x-* , name[*] , test-*")
        self.assertEqual(result, ["x-*", "name[*]", "test-*"])

    def test_empty_patterns_filtered_out(self):
        result = parse_ignore_patterns("x-*,,name[*],")
        self.assertEqual(result, ["x-*", "name[*]"])

    def test_only_whitespace_patterns_filtered_out(self):
        result = parse_ignore_patterns("x-*,   ,name[*]")
        self.assertEqual(result, ["x-*", "name[*]"])


class TestShouldIgnoreField(unittest.TestCase):
    """Tests for should_ignore_field function."""

    def test_empty_patterns_never_ignores(self):
        self.assertFalse(should_ignore_field("x-test", []))

    def test_exact_match(self):
        self.assertTrue(should_ignore_field("x-test", ["x-test"]))

    def test_wildcard_prefix(self):
        self.assertTrue(should_ignore_field("x-test", ["x-*"]))
        self.assertTrue(should_ignore_field("x-internal-id", ["x-*"]))
        self.assertFalse(should_ignore_field("test", ["x-*"]))

    def test_wildcard_suffix(self):
        self.assertTrue(should_ignore_field("test-field", ["*-field"]))
        self.assertFalse(should_ignore_field("test-other", ["*-field"]))

    def test_wildcard_middle(self):
        self.assertTrue(should_ignore_field("name[en_EN]", ["name[*]"]))
        self.assertTrue(should_ignore_field("name[ar]", ["name[*]"]))
        self.assertFalse(should_ignore_field("other[en_EN]", ["name[*]"]))

    def test_multiple_patterns(self):
        patterns = ["x-*", "name[*]"]
        self.assertTrue(should_ignore_field("x-test", patterns))
        self.assertTrue(should_ignore_field("name[en_EN]", patterns))
        self.assertFalse(should_ignore_field("regular-field", patterns))

    def test_question_mark_wildcard(self):
        self.assertTrue(should_ignore_field("x-a", ["x-?"]))
        self.assertFalse(should_ignore_field("x-ab", ["x-?"]))


class TestFilterIgnoredFields(unittest.TestCase):
    """Tests for filter_ignored_fields function."""

    def test_empty_patterns_returns_original(self):
        data = {"x-test": "value", "name": "test"}
        result = filter_ignored_fields(data, [])
        self.assertEqual(result, data)

    def test_filter_top_level_fields(self):
        data = {"x-test": "value", "name": "test", "x-internal": "secret"}
        result = filter_ignored_fields(data, ["x-*"])
        self.assertEqual(result, {"name": "test"})

    def test_filter_nested_fields(self):
        data = {
            "asset": {
                "id": 1,
                "x-test": "value",
                "name[en_En]": "Test",
            },
            "x-external": "outer",
        }
        result = filter_ignored_fields(data, ["x-*", "name[*]"])
        expected = {"asset": {"id": 1}}
        self.assertEqual(result, expected)

    def test_filter_deeply_nested_fields(self):
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "x-deep": "value",
                        "keep": "this",
                    }
                }
            }
        }
        result = filter_ignored_fields(data, ["x-*"])
        expected = {"level1": {"level2": {"level3": {"keep": "this"}}}}
        self.assertEqual(result, expected)

    def test_filter_in_list_of_dicts(self):
        data = {
            "items": [
                {"id": 1, "x-test": "a"},
                {"id": 2, "x-test": "b"},
            ]
        }
        result = filter_ignored_fields(data, ["x-*"])
        expected = {"items": [{"id": 1}, {"id": 2}]}
        self.assertEqual(result, expected)

    def test_primitives_unchanged(self):
        self.assertEqual(filter_ignored_fields("string", ["x-*"]), "string")
        self.assertEqual(filter_ignored_fields(123, ["x-*"]), 123)
        self.assertEqual(filter_ignored_fields(None, ["x-*"]), None)
        self.assertEqual(filter_ignored_fields(True, ["x-*"]), True)

    def test_list_of_primitives_unchanged(self):
        data = [1, 2, 3, "test"]
        result = filter_ignored_fields(data, ["x-*"])
        self.assertEqual(result, data)

    def test_complex_nested_structure(self):
        data = {
            "x-root": "ignored",
            "users": [
                {
                    "id": 1,
                    "x-internal": "ignored",
                    "profile": {
                        "name": "John",
                        "name[en_EN]": "John",
                        "x-metadata": {"key": "value"},
                    },
                }
            ],
            "meta": {"x-version": "1.0", "timestamp": 12345},
        }
        result = filter_ignored_fields(data, ["x-*", "name[*]"])
        expected = {
            "users": [
                {
                    "id": 1,
                    "profile": {"name": "John"},
                }
            ],
            "meta": {"timestamp": 12345},
        }
        self.assertEqual(result, expected)

    def test_empty_dict_after_filtering(self):
        data = {"x-only": "value"}
        result = filter_ignored_fields(data, ["x-*"])
        self.assertEqual(result, {})

    def test_empty_nested_dict_after_filtering(self):
        data = {"parent": {"x-only": "value"}}
        result = filter_ignored_fields(data, ["x-*"])
        self.assertEqual(result, {"parent": {}})


class TestIntegration(unittest.TestCase):
    """Integration tests for the full filtering workflow."""

    def test_parse_and_filter(self):
        ignore_fields = "x-*,name[*]"
        patterns = parse_ignore_patterns(ignore_fields)

        data = {
            "id": 1,
            "x-test": "ignored",
            "name[en_EN]": "ignored",
            "name": "kept",
        }

        result = filter_ignored_fields(data, patterns)
        expected = {"id": 1, "name": "kept"}
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
