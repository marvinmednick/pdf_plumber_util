"""JSON utilities with performance optimizations.

This module provides a high-performance JSON interface using orjson
while maintaining compatibility with the standard json module interface.
Falls back to standard json if orjson is not available.
"""

import json as _stdlib_json
from typing import Any, Dict, TextIO, Union
from pathlib import Path

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False


def dumps(obj: Any, indent: Union[int, None] = None) -> str:
    """Serialize object to JSON string with performance optimization.
    
    Args:
        obj: Object to serialize
        indent: Indentation level (None for compact, int for pretty-printed)
    
    Returns:
        JSON string
    """
    if HAS_ORJSON:
        # orjson returns bytes, need to decode to string
        if indent is not None:
            # orjson uses OPT_INDENT_2 for pretty printing (2-space indent)
            return orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode('utf-8')
        else:
            return orjson.dumps(obj).decode('utf-8')
    else:
        return _stdlib_json.dumps(obj, indent=indent)


def dump(obj: Any, fp: TextIO, indent: Union[int, None] = None) -> None:
    """Serialize object to JSON file with performance optimization.
    
    Args:
        obj: Object to serialize
        fp: File-like object to write to
        indent: Indentation level (None for compact, int for pretty-printed)
    """
    if HAS_ORJSON:
        # orjson doesn't have a direct dump() method, so we use dumps() + write
        json_str = dumps(obj, indent=indent)
        fp.write(json_str)
    else:
        _stdlib_json.dump(obj, fp, indent=indent)


def loads(s: str) -> Any:
    """Deserialize JSON string to Python object.
    
    Args:
        s: JSON string to deserialize
    
    Returns:
        Deserialized Python object
    """
    if HAS_ORJSON:
        return orjson.loads(s)
    else:
        return _stdlib_json.loads(s)


def load(fp: TextIO) -> Any:
    """Deserialize JSON file to Python object.
    
    Args:
        fp: File-like object to read from
    
    Returns:
        Deserialized Python object
    """
    if HAS_ORJSON:
        content = fp.read()
        return orjson.loads(content)
    else:
        return _stdlib_json.load(fp)


# For compatibility with json.JSONDecodeError
JSONDecodeError = _stdlib_json.JSONDecodeError


def get_json_backend() -> str:
    """Get the name of the JSON backend being used.
    
    Returns:
        'orjson' if orjson is available and being used, 'json' otherwise
    """
    return 'orjson' if HAS_ORJSON else 'json'