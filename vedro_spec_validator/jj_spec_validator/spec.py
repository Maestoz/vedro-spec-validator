from typing import Any

import json
import yaml


from ._config import Config
from urllib.parse import urlparse
from pathlib import Path
import httpx

from schemax import SchemaData, collect_schema_data

from .output import output
from .utils._cacheir import validate_cache_file, save_cache, load_cache


class SchemaParseError(Exception):
    """Raised when a spec cannot be parsed into a schema."""
    pass

class Spec:
    def __init__(self,
                 spec_link: str,
                 func_name: str,
                 skip_if_failed_to_get_spec: bool = False,
                 is_strict: bool = False,
                 force_strict: bool = False,
                 ):
        self.spec_link = spec_link
        self.func_name = func_name
        self.skip_if_failed_to_get_spec = skip_if_failed_to_get_spec
        self.is_strict = is_strict
        self.force_strict = force_strict

    def _download_spec(self) -> httpx.Response | None:
        def handle_exception(exc: Exception, message: str = ""):
            if self.skip_if_failed_to_get_spec:
                output(func_name=self.func_name, e=exc, text=message)
                return None
            else:
                exc.args = (message,) + exc.args[1:] if exc.args else (message,)
                raise exc
        try:
            response = httpx.get(self.spec_link, timeout=Config.GET_SPEC_TIMEOUT)
            response.raise_for_status()
            return response

        except httpx.ConnectTimeout as e:
            return handle_exception(
                e, f"Timeout occurred while trying to connect to the {self.spec_link}.")
        except httpx.ReadTimeout as e:
            return handle_exception(
                e, f"Timeout occurred while trying to read the spec from the {self.spec_link}.")
        except httpx.HTTPStatusError as e:
            return handle_exception(e)
        except httpx.HTTPError as e:
            return handle_exception(
                e, f"An HTTP error occurred while trying to download the {self.spec_link}")
        except Exception as e:
            return handle_exception(
                e, f"An unexpected error occurred while trying to download the {self.spec_link}")

    def _parse_spec(self, response: httpx.Response) -> dict[str, Any]:
        content_type = response.headers.get('Content-Type', '')

        if 'application/json' in content_type:
            raw_spec = json.loads(response.text)
        elif 'text/yaml' in content_type or 'application/x-yaml' in content_type:
            raw_spec = yaml.load(response.text, Loader=yaml.CLoader)
        else:
            # trying to match via file extension
            if self.spec_link.endswith('.json'):
                raw_spec = json.loads(response.text)
            elif self.spec_link.endswith('.yaml') or self.spec_link.endswith('.yml'):
                raw_spec = yaml.load(response.text, Loader=yaml.CLoader)
            else:
                raise ValueError(f"Unsupported content type: {content_type}")
        return raw_spec

    def _get_schema_from_json(self, raw_spec: dict[str, Any]) -> list[SchemaData]:
        try:
            schema_data = collect_schema_data(raw_spec)
        except Exception as e:
            raise SchemaParseError(
                f"Failed to parse {self.spec_link} to schema via schemax.\n"
                f"Probably the spec is broken or has an unsupported format.\n"
                f"Original exception: {e}")
        return schema_data

    def _build_dict_of_schemas(self, schema_data: list[SchemaData]) -> dict[tuple[str, str, str], SchemaData]:
        entity_dict = {}
        if len(schema_data) == 0:
            raise ValueError("Empty list of entities provided.")
        for elem in schema_data:
            if not isinstance(elem, SchemaData):
                raise TypeError(f"Expected SchemaData, got {type(elem)}")
            entity_key = (elem.http_method.upper(), elem.path, elem.status)
            entity_dict[entity_key] = elem
        return entity_dict

    def _get_raw_spec_from_file(self) -> dict[str, Any]:
        path = Path(self.spec_link)
        if not path.exists():
            raise FileNotFoundError(f"Specification file not found: {self.spec_link}")

        with open(path, 'r') as f:
            if path.suffix == '.json':
                raw_spec = json.loads(f.read())
            elif path.suffix in ('.yml', '.yaml'):
                raw_spec = yaml.load(f.read(), Loader=yaml.CLoader)
            else:
                raise ValueError(f"Unsupported file format: {path.suffix}")
        return raw_spec

    def get_prepared_spec_units(self) -> dict[tuple[str, str, str], SchemaData] | None:
        if self.spec_link is None:
            raise ValueError("Spec link cannot be None")

        if urlparse(self.spec_link).scheme in ('http', 'https', 'ftp') and urlparse(self.spec_link).netloc:
            if validate_cache_file(self.spec_link):
                raw_spec = load_cache(self.spec_link)
            else:
                response = self._download_spec()
                if response is None:
                    return None
                raw_spec = self._parse_spec(response)
                save_cache(spec_link=self.spec_link, raw_schema=raw_spec)
            schema_data = self._get_schema_from_json(raw_spec)
            return self._build_dict_of_schemas(schema_data)
        elif Path(self.spec_link).is_absolute():
            raw_spec = self._get_raw_spec_from_file()
            schema_data = self._get_schema_from_json(raw_spec)
            return self._build_dict_of_schemas(schema_data)
        else:
            raise ValueError(f"{self.spec_link} is neither a valid URL nor a valid path")
        