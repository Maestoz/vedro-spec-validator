import re
from typing import Any, Match

from d42.declaration import GenericSchema
from d42.substitution import SubstitutorValidator
from d42.validation import ValidationException, format_result

__all__ = ('normalize_path', 'destroy_prefix', 'validate_non_strict', )


def normalize_path(path: str) -> str:
    var_counter = 1

    def replace_var(match: Match[str]) -> str:
        nonlocal var_counter
        replacement = f'{{var{var_counter}}}'
        var_counter += 1
        return replacement

    normalized_path = re.sub(r'{[a-zA-Z0-9_]+}', replace_var, path)

    return normalized_path

def destroy_prefix(path: str, prefix: str) -> str:
    return re.sub(prefix, '', path)

def validate_non_strict(schema: GenericSchema, value: dict[str, Any]) -> bool:
    result = schema.__accept__(SubstitutorValidator(), value=value)
    if errors := format_result(result):
        raise ValidationException("\n".join(errors))
    return True
