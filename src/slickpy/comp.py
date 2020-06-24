import sys

if sys.version_info[:2] < (3, 7):
    from asyncio import (
        _get_running_loop as get_running_loop,
    )  # pragma: nocover
else:
    from asyncio import get_running_loop  # pragma: nocover


__all__ = ("get_running_loop",)
