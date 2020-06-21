import typing

# ASGI
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]
ASGICallable = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]

# router
HTTPMethods = typing.Tuple[str, ...]
RouteMatch = typing.Tuple[ASGICallable, HTTPMethods]
ExactMatches = typing.Dict[str, RouteMatch]
RegexMatches = typing.List[typing.Tuple[typing.Pattern[str], RouteMatch]]
RouteResult = typing.Tuple[ExactMatches, RegexMatches]
RouteAdapter = typing.Callable[
    [str, ASGICallable, HTTPMethods], typing.Optional[RouteResult]
]

# response
Headers = typing.List[typing.Tuple[bytes, bytes]]

# lifespan
LifespanSubscriber = typing.Callable[[], typing.Awaitable[None]]

# middleware
Middleware = typing.Callable[[ASGICallable], ASGICallable]

# application
AnyAsyncCallable = typing.Callable[..., typing.Awaitable[typing.Any]]
ASGIAdapter = typing.Callable[
    [AnyAsyncCallable], typing.Optional[ASGICallable]
]
