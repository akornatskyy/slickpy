import platform

if platform.python_implementation() == "PyPy":  # pragma: nocover
    from json import dumps as json_dumps, loads as json_loads
else:  # pragma: nocover
    try:
        from ujson import (  # type: ignore[assignment]
            dumps as json_dumps,
            loads as json_loads,
        )
    except ImportError:  # pragma: nocover
        from json import dumps as json_dumps, loads as json_loads


__all__ = ("json_dumps", "json_loads")
