import json
from hashlib import md5
from os import makedirs, path, remove
from pickle import dump
from pickle import load as pickle_load
from time import time
from typing import Any, Dict, Tuple


from .._config import Config


CACHE_DIR = Config.MAIN_DIRECTORY + '/_cache_parsed_specs'
CACHE_TTL = 3600  # in second


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
