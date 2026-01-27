"""Field filtering utilities for ignoring specific fields during validation."""

import re
from typing import Any


def parse_ignore_patterns(ignore_fields: str) -> list[str]:
    """Parse comma-separated wildcard patterns into a list.

    Args:
        ignore_fields: Comma-separated wildcard patterns, e.g. "x-*,name[*]"

    Returns:
        List of trimmed non-empty patterns.
    """
    if not ignore_fields:
        return []
    return [pattern.strip() for pattern in ignore_fields.split(",") if pattern.strip()]


def _pattern_to_regex(pattern: str) -> re.Pattern[str]:
    """Convert a wildcard pattern to a compiled regex.

    Supports:
        * - matches any sequence of characters
        ? - matches any single character

    Args:
        pattern: Wildcard pattern like "x-*" or "name[*]"

    Returns:
        Compiled regex pattern.
    """
    # Escape all regex special characters except * and ?
    regex_pattern = ""
    for char in pattern:
        if char == "*":
            regex_pattern += ".*"
        elif char == "?":
            regex_pattern += "."
        else:
            regex_pattern += re.escape(char)

    return re.compile(f"^{regex_pattern}$")


def should_ignore_field(field_name: str, patterns: list[str]) -> bool:
    """Check if a field name matches any of the ignore patterns.

    Args:
        field_name: The name of the field to check.
        patterns: List of wildcard patterns to match against.

    Returns:
        True if the field should be ignored, False otherwise.
    """
    return any(_pattern_to_regex(pattern).match(field_name) for pattern in patterns)


def filter_ignored_fields(data: Any, patterns: list[str]) -> Any:
    """Recursively filter out fields matching ignore patterns from data.

    Args:
        data: The data structure to filter (dict, list, or primitive).
        patterns: List of wildcard patterns for fields to ignore.

    Returns:
        Filtered data with matching fields removed.
    """
    if not patterns:
        return data

    if isinstance(data, dict):
        return {
            key: filter_ignored_fields(value, patterns)
            for key, value in data.items()
            if not should_ignore_field(key, patterns)
        }

    if isinstance(data, list):
        return [filter_ignored_fields(item, patterns) for item in data]

    return data
