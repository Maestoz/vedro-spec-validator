import json
from hashlib import md5
from os import makedirs, path, remove
from pickle import dump
from pickle import load as pickle_load
from time import time
from typing import Any, Dict, Tuple
from urllib.parse import urlparse
from pathlib import Path

import httpx
from schemax import SchemaData, collect_schema_data
from yaml import CLoader, load

from .._config import Config
from ..validator_base import BaseValidator


CACHE_DIR = Config.MAIN_DIRECTORY + '/_cache_parsed_specs'
CACHE_TTL = 3600  # in second


# def _build_entity_dict(entities: list[SchemaData]) -> dict[tuple[str, str, str], SchemaData]:
#     entity_dict = {}
#     if len(entities) == 0:
#         raise ValueError("Empty list of entities provided.")
#     for entity in entities:
#         if not isinstance(entity, SchemaData):
#             raise TypeError(f"Expected SchemaData, got {type(entity)}")
#         entity_key = (entity.http_method.upper(), entity.path, entity.status)
#         entity_dict[entity_key] = entity
#     return entity_dict

def _get_cache_filename(url: str) -> str:
    hash_obj = md5(url.encode())
    return path.join(CACHE_DIR, hash_obj.hexdigest() + '.cache')

def validate_cache_file(spec_link: str) -> bool:
    filename = _get_cache_filename(spec_link)
    if not path.isfile(filename):
        return False

    file_age = time() - path.getmtime(filename)

    if file_age > CACHE_TTL:
        remove(filename)
        return False

    return True


# def _download_spec(validator: BaseValidator) -> httpx.Response | None:
#     def handle_exception(exc: Exception, message: str):
#         if validator.skip_if_failed_to_get_spec:
#             validator.output(exc, message)
#             return None
#         else:
#             raise type(exc)(message) from exc
#     try:
#         response = httpx.get(validator.spec_link, timeout=Config.GET_SPEC_TIMEOUT)
#         response.raise_for_status()
#         return response
#
#     except httpx.ConnectTimeout as e:
#         return handle_exception(
#             e, f"Timeout occurred while trying to connect to the {validator.spec_link}.")
#     except httpx.ReadTimeout as e:
#         return handle_exception(
#             e, f"Timeout occurred while trying to read the spec from the {validator.spec_link}.")
#     except httpx.HTTPStatusError as e:
#         status_code = e.response.status_code
#         if 400 <= status_code < 500:
#             return handle_exception(e, f"Client error occurred: {status_code} {e.response.reason_phrase}")
#         elif 500 <= status_code < 600:
#             return handle_exception(e, f"Server error occurred: {status_code} {e.response.reason_phrase}")
#     except httpx.HTTPError as e:
#         return handle_exception(
#             e, f"An HTTP error occurred while trying to download the {validator.spec_link}: {e}")
#     except Exception as e:
#         return handle_exception(
#             e, f"An unexpected error occurred while trying to download the {validator.spec_link}: {e}")


def save_cache(spec_link: str, raw_schema: dict[str, Any]) -> None:
    if not spec_link or not spec_link.strip():
        raise ValueError("spec_link must be a non-empty string")
    filename = _get_cache_filename(spec_link)
    makedirs(CACHE_DIR, exist_ok=True)
    with open(filename, 'wb') as f:
        dump(raw_schema, f)

def load_cache(spec_link: str) -> dict[str, Any]:
    filename = _get_cache_filename(spec_link)
    with open(filename, 'rb') as f:
        raw_spec = pickle_load(f)

    return raw_spec

# def load_cache(validator: BaseValidator) -> Dict[Tuple[str, str, str], SchemaData] | None:
#     filename = _get_cache_filename(validator.spec_link)
#
#     if _validate_cache_file(filename):
#         with open(filename, 'rb') as f:
#             raw_schema = pickle_load(f)
#     else:
#         parsed_url = urlparse(validator.spec_link)
#
#         if not parsed_url.scheme:
#             path = Path(validator.spec_link)
#             if not path.exists():
#                 raise FileNotFoundError(f"Specification file not found: {validator.spec_link}")
#
#             with open(path, 'r') as f:
#                 if path.suffix == '.json':
#                     raw_schema = json.loads(f.read())
#                 elif path.suffix in ('.yml', '.yaml'):
#                     raw_schema = load(f.read(), Loader=CLoader)
#                 else:
#                     raise ValueError(f"Unsupported file format: {path.suffix}")
#         else:
#             raw_spec = _download_spec(validator)
#             if raw_spec is None:
#                 return None
#
#             content_type = raw_spec.headers.get('Content-Type', '')
#
#             if 'application/json' in content_type:
#                 raw_schema = json.loads(raw_spec.text)
#             elif 'text/yaml' in content_type or 'application/x-yaml' in content_type:
#                 raw_schema = load(raw_spec.text, Loader=CLoader)
#             else:
#                 # trying to match via file extension
#                 if validator.spec_link.endswith('.json'):
#                     raw_schema = json.loads(raw_spec.text)
#                 elif validator.spec_link.endswith('.yaml') or validator.spec_link.endswith('.yml'):
#                     raw_schema = load(raw_spec.text, Loader=CLoader)
#                 else:
#                     raise ValueError(f"Unsupported content type: {content_type}")
#
#         _save_cache(validator.spec_link, raw_schema)
#
#     try:
#         parsed_data = collect_schema_data(raw_schema)
#     except Exception as e:
#         raise Exception(f"Failed to parse spec to schema via schemax.\nProbably the spec is broken or has an unsupported format.\nException: {e}")
#     prepared_dict = _build_entity_dict(parsed_data)
#
#     return prepared_dict
