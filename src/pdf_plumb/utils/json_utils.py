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

    For top-level lists, writes one element at a time so the full
    serialized JSON is never held in memory at once (large per-page
    result lists like raw_words_by_page can otherwise use several GB).

    Args:
        obj: Object to serialize
        fp: File-like object to write to
        indent: Indentation level (None for compact, int for pretty-printed)
    """
    if HAS_ORJSON:
        if isinstance(obj, list):
            _dump_list_streaming(obj, fp, indent=indent)
        else:
            # orjson doesn't have a direct dump() method, so we use dumps() + write
            json_str = dumps(obj, indent=indent)
            fp.write(json_str)
    else:
        _stdlib_json.dump(obj, fp, indent=indent)


def _dump_list_streaming(items: list, fp: TextIO, indent: Union[int, None] = None) -> None:
    """Write a list to fp as a JSON array, serializing one element at a time.

    Produces output equivalent to orjson.dumps(items, option=OPT_INDENT_2)
    without ever materializing the full array's JSON in memory.
    """
    if not items:
        fp.write("[]")
        return

    pad = " " * indent if indent else ""
    fp.write("[\n" if indent else "[")
    for i, item in enumerate(items):
        if indent:
            item_json = orjson.dumps(item, option=orjson.OPT_INDENT_2).decode('utf-8')
            item_json = "\n".join(pad + line for line in item_json.split("\n"))
        else:
            item_json = orjson.dumps(item).decode('utf-8')
        if i > 0:
            fp.write(",\n" if indent else ",")
        fp.write(item_json)
    fp.write("\n]" if indent else "]")


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


def save_json(data: Any, filepath: Union[str, Path], indent: Union[int, None] = 2) -> None:
    """Save data to JSON file with performance optimization.
    
    Args:
        data: Data to serialize and save
        filepath: Path where to save the JSON file
        indent: Indentation level (None for compact, int for pretty-printed)
    """
    filepath = Path(filepath)
    with open(filepath, 'w', encoding='utf-8') as f:
        dump(data, f, indent=indent)


def get_json_backend() -> str:
    """Get the name of the JSON backend being used.
    
    Returns:
        'orjson' if orjson is available and being used, 'json' otherwise
    """
    return 'orjson' if HAS_ORJSON else 'json'