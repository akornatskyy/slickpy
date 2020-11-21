import re
import typing

from slickpy.typing import (
    ASGICallable,
    ExactMatches,
    HTTPMethods,
    RegexMatches,
    RouteAdapter,
    RouteMatch,
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
        exact_patterns, regex_patterns = route(pattern)
        route_match = {method: handler for method in methods}
        merge_exact_matches(self.exact_matches, exact_patterns, route_match)
        merge_regex_matches(self.regex_matches, regex_patterns, route_match)


def merge_exact_matches(
    exact_matches: ExactMatches,
    patterns: typing.List[str],
    route_match: RouteMatch,
) -> None:
    for pattern in patterns:
        m = exact_matches.get(pattern)
        if m:
            m.update(route_match)
        else:
            exact_matches[pattern] = route_match


def merge_regex_matches(
    regex_matches: RegexMatches,
    patterns: typing.List[typing.Pattern[str]],
    route_match: RouteMatch,
) -> None:
    for pattern in patterns:
        for p, m in regex_matches:
            if pattern.pattern == p.pattern:
                m.update(route_match)
        else:
            regex_matches.append((pattern, route_match))


def route(pattern: str) -> RouteResult:
    for pattern_adapter in pattern_adapters:
        r = pattern_adapter(pattern)
        if r:
            return r
    else:  # pragma: nocover
        # unreachable code since regex route unconditionally returns
        # a compiled patter or fails to compile
        raise AssertionError(f"unable to find adapter for pattern '{pattern}'")


@register_route_adapter
def regex_route(pattern: str) -> typing.Optional[RouteResult]:
    return [], [re.compile(pattern)]


RE_PLAIN_ROUTE = re.compile(r"^[\w./-]+$")


@register_route_adapter
def plain_route(pattern: str) -> typing.Optional[RouteResult]:
    if pattern == "" or RE_PLAIN_ROUTE.match(pattern):
        return [pattern], []
    return None
