import re
import typing

from slickpy.typing import (
    ASGICallable,
    ExactMatches,
    HTTPMethods,
    RegexMatches,
    RouteAdapter,
    RouteResult,
)

pattern_adapters: typing.List[RouteAdapter] = []


def register_route_adapter(fn: RouteAdapter) -> None:
    pattern_adapters.insert(0, fn)


class Router(object):
    def __init__(self) -> None:
        self.exact_matches: ExactMatches = {}
        self.regex_matches: RegexMatches = []

    def add(
        self,
        pattern: str,
        handler: ASGICallable,
        *,
        methods: HTTPMethods = ("GET", "HEAD"),
    ) -> None:
        exact_matches, regex_matches = route(pattern, handler, methods=methods)
        self.exact_matches.update(exact_matches)
        self.regex_matches.extend(regex_matches)


def route(
    pattern: str,
    handler: ASGICallable,
    *,
    methods: HTTPMethods = ("GET", "HEAD"),
) -> RouteResult:
    for pattern_adapter in pattern_adapters:
        r = pattern_adapter(pattern, handler, methods)
        if r:
            return r
    else:  # pragma: nocover
        # unreachable code since regex route unconditionally returns
        # a compiled patter or fails to compile
        raise AssertionError(f"unable to find adapter for pattern '{pattern}'")


@register_route_adapter
def regex_route(
    pattern: str, handler: ASGICallable, http_verbs: HTTPMethods,
) -> typing.Optional[RouteResult]:
    return {}, [(re.compile(pattern), (handler, http_verbs))]


RE_PLAIN_ROUTE = re.compile(r"^[\w./-]+$")


@register_route_adapter
def plain_route(
    pattern: str, handler: ASGICallable, http_verbs: HTTPMethods,
) -> typing.Optional[RouteResult]:
    if pattern == "" or RE_PLAIN_ROUTE.match(pattern):
        return {pattern: (handler, http_verbs)}, []
    return None
