import inspect
import typing

from slickpy.lifespan import Lifespan
from slickpy.middleware.routing import RoutingMiddleware
from slickpy.request import Request
from slickpy.response import Writer
from slickpy.router import Router
from slickpy.typing import (
    ASGIAdapter,
    ASGICallable,
    AnyAsyncCallable,
    LifespanSubscriber,
    Middleware,
    Receive,
    Scope,
    Send,
)

asgi_adapters: typing.List[ASGIAdapter] = []


def register_asgi_adapter(fn: ASGIAdapter) -> None:
    asgi_adapters.insert(0, fn)


class App(object):
    def __init__(self) -> None:
        self.router = Router()
        self.lifespan = Lifespan()
        self.middleware: ASGICallable = RoutingMiddleware(self.router)

    def use(self, middleware: Middleware) -> None:
        self.middleware = middleware(self.middleware)

    def route(
        self,
        pattern: str,
        *,
        methods: typing.Tuple[str, ...] = ("GET", "HEAD"),
    ) -> typing.Callable[[AnyAsyncCallable], None]:
        def decorator(handler: AnyAsyncCallable) -> None:
            for asgi_adapter in asgi_adapters:
                asgi_callable = asgi_adapter(handler)
                if asgi_callable:
                    self.router.add(pattern, asgi_callable, methods=methods)
                    break
            else:
                raise AssertionError(
                    f"unable to find asgi adapter for pattern '{pattern}'"
                )

        return decorator

    def on(self, event: str) -> typing.Callable[[LifespanSubscriber], None]:
        def decorator(subscriber: LifespanSubscriber) -> None:
            self.lifespan.add(event, subscriber)

        return decorator

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
        else:
            await self.middleware(scope, receive, send)


# region: internal details

WCallable = typing.Callable[[Writer], typing.Awaitable[None]]
WReqCallable = typing.Callable[[Writer, Request], typing.Awaitable[None]]
NoReqCallable = typing.Callable[[], typing.Awaitable[ASGICallable]]
ReqCallable = typing.Callable[[Request], typing.Awaitable[ASGICallable]]


@register_asgi_adapter
def handler_adapter(
    handler: AnyAsyncCallable,
) -> typing.Optional[ASGICallable]:
    if not inspect.isfunction(handler):
        return None
    parameters = tuple(name for name in inspect.signature(handler).parameters)
    if parameters == ("scope", "receive", "send"):
        return typing.cast(ASGICallable, handler)
    if parameters == ("w",):
        return w_adapter(typing.cast(WCallable, handler))
    if parameters == ("w", "req"):
        return w_req_adapter(typing.cast(WReqCallable, handler))
    if parameters == ("req",):
        return req_adapter(typing.cast(ReqCallable, handler))
    if parameters == ():
        return no_req_adapter(typing.cast(NoReqCallable, handler))
    return None


def w_req_adapter(handler: WReqCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        await handler(Writer(send), Request(scope))

    return asgi


def w_adapter(handler: WCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        await handler(Writer(send))

    return asgi


def req_adapter(handler: ReqCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        res = await handler(Request(scope))
        await res(scope, receive, send)

    return asgi


def no_req_adapter(handler: NoReqCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        res = await handler()
        await res(scope, receive, send)

    return asgi
