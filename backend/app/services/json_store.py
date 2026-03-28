import copy
import json
import os
import threading
import time
from pathlib import Path
from typing import Any

_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = threading.Lock()

def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    mtime = path.stat().st_mtime
    with _cache_lock:
        cached = _cache.get(str(path))
        if cached and cached[0] == mtime:
            return copy.deepcopy(cached[1])
    with open(path) as f:
        data = json.load(f)
    with _cache_lock:
        _cache[str(path)] = (mtime, data)
    return copy.deepcopy(data)

def write_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix('.tmp')
    with open(tmp, 'w') as f:
        json.dump(data, f, indent=2)
    os.rename(tmp, path)
    with _cache_lock:
        _cache[str(path)] = (path.stat().st_mtime, copy.deepcopy(data))
