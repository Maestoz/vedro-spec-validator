import json
from hashlib import md5
from os import makedirs, path, remove
from pickle import dump
from pickle import load as pickle_load
from time import time
from typing import Any, Dict, List, Tuple
from pathlib import Path
from urllib.parse import urlparse

import httpx
from schemax import SchemaData, collect_schema_data
from yaml import CLoader, load

from .._config import Config
from ..validator_base import BaseValidator

__all__ = ('load_cache', )

CACHE_DIR = Config.MAIN_DIRECTORY + '/_cache_parsed_specs'
CACHE_TTL = 3600  # in second


def _build_entity_dict(entities: List[SchemaData]) -> Dict[Tuple[str, str, str], SchemaData]:
    entity_dict = {}
    for entity in entities:
        entity_key = (entity.http_method.upper(), entity.path, entity.status)
        entity_dict[entity_key] = entity
    return entity_dict


def _validate_cache_file(filename: str) -> bool:
    if not path.isfile(filename):
        return False

    file_age = time() - path.getmtime(filename)

    if file_age > CACHE_TTL:
        remove(filename)
        return False

    return True


def _get_cache_filename(url: str) -> str:
    hash_obj = md5(url.encode())
    return path.join(CACHE_DIR, hash_obj.hexdigest() + '.cache' + '.yml')


def _download_spec(validator: BaseValidator) -> httpx.Response | None:
    response = None
    if validator.skip_if_failed_to_get_spec:
        try:
            response = httpx.get(validator.spec_link, timeout=Config.GET_SPEC_TIMEOUT)
            response.raise_for_status()
        except httpx.ConnectTimeout as e:
            validator.output(e, f"Timeout occurred while trying to connect to the {validator.spec_link}.")
            return None
        except httpx.ReadTimeout as e:
            validator.output(e, f"Timeout occurred while trying to read the spec from the {validator.spec_link}.")
            return None
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if 400 <= status_code < 500:
                validator.output(e, f"Client error occurred: {status_code} {e.response.reason_phrase}")
                return None
            elif 500 <= status_code < 600:
                validator.output(e, f"Server error occurred: {status_code} {e.response.reason_phrase}")
                return None
        except httpx.HTTPError as e:
            validator.output(e, f"An error occurred while trying to download the spec: {e}")
            return None
        except Exception as e:
            validator.output(e, f"An error occurred while trying to download the spec: {e}")
            return None
        return response
    else:
        try:
            response = httpx.get(validator.spec_link, timeout=Config.GET_SPEC_TIMEOUT)
            response.raise_for_status()
        except httpx.ConnectTimeout:
            raise httpx.ConnectTimeout(f"Timeout occurred while trying to connect to the {validator.spec_link}.")
        except httpx.ReadTimeout:
            raise httpx.ReadTimeout(f"Timeout occurred while trying to read the spec from the {validator.spec_link}.")
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if 400 <= status_code < 500:
                raise ValueError(f"Client error occurred: {status_code} {e.response.reason_phrase}")
            elif 500 <= status_code < 600:
                raise RuntimeError(f"Server error occurred: {status_code} {e.response.reason_phrase}")
        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"An error occurred while trying to download the spec: {e}")
        except Exception as e:
            raise ValueError(f"An error occurred while trying to download the spec: {e}")

        return response


def _save_cache(spec_link: str, raw_schema: dict[str, Any]) -> None:
    filename = _get_cache_filename(spec_link)
    makedirs(CACHE_DIR, exist_ok=True)
    with open(filename, 'wb') as f:
        dump(raw_schema, f)


def load_cache(validator: BaseValidator) -> Dict[Tuple[str, str, str], SchemaData] | None:
    filename = _get_cache_filename(validator.spec_link)

    if _validate_cache_file(filename):
        with open(filename, 'rb') as f:
            raw_schema = pickle_load(f)
    else:
        parsed_url = urlparse(validator.spec_link)
        
        if not parsed_url.scheme:
            path = Path(validator.spec_link)
            if not path.exists():
                raise FileNotFoundError(f"Specification file not found: {validator.spec_link}")
                
            with open(path, 'r') as f:
                if path.suffix == '.json':
                    raw_schema = json.loads(f.read())
                elif path.suffix in ('.yml', '.yaml'):
                    raw_schema = load(f.read(), Loader=CLoader)
                else:
                    raise ValueError(f"Unsupported file format: {path.suffix}")
        else:
            raw_spec = _download_spec(validator)
            if raw_spec is None:
                return None

            content_type = raw_spec.headers.get('Content-Type', '')

            if 'application/json' in content_type:
                raw_schema = json.loads(raw_spec.text)
            elif 'text/yaml' in content_type or 'application/x-yaml' in content_type:
                raw_schema = load(raw_spec.text, Loader=CLoader)
            else:
                # trying to match via file extension
                if validator.spec_link.endswith('.json'):
                    raw_schema = json.loads(raw_spec.text)
                elif validator.spec_link.endswith('.yaml') or validator.spec_link.endswith('.yml'):
                    raw_schema = load(raw_spec.text, Loader=CLoader)
                else:
                    raise ValueError(f"Unsupported content type: {content_type}")

        _save_cache(validator.spec_link, raw_schema)

    parsed_data = collect_schema_data(raw_schema)
    prepared_dict = _build_entity_dict(parsed_data)

    return prepared_dict
