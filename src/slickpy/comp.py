import sys
import typing

if sys.version_info[:2] < (3, 7):
    from asyncio import (  # pragma: nocover
        _get_running_loop as get_running_loop,
    )
else:
    from asyncio import get_running_loop  # pragma: nocover

try:
    from ujson import dumps as ujson_dumps, loads as ujson_loads
except ImportError:  # pragma: nocover

    def ujson_dumps(  # noqa: CFQ002
        obj: typing.Any,
        ensure_ascii: bool = True,
        double_precision: int = 0,
        encode_html_chars: bool = False,
        escape_forward_slashes: bool = True,
        sort_keys: bool = False,
        indent: int = 0,
    ) -> str:
        raise AssertionError("The 'ujson' package must be installed.")

    def ujson_loads(
        s: typing.AnyStr,
        precise_float: bool = True,
    ) -> typing.Any:
        raise AssertionError("The 'ujson' package must be installed.")


__all__ = ("get_running_loop", "ujson_dumps", "ujson_loads")
