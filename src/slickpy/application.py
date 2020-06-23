import inspect
import typing

from slickpy.lifespan import Lifespan
from slickpy.middleware.routing import RoutingMiddleware
from slickpy.request import Request
from slickpy.response import BinaryResponse, Response, TextResponse, Writer
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
        self.entry: ASGICallable = RoutingMiddleware(
            self.router, self.lifespan
        )

    def middleware(self, m: Middleware) -> None:
        self.entry = m(self.entry)

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

    def asgi(self) -> ASGICallable:
        return self.entry


# region: internal details

WCallable = typing.Callable[[Writer], typing.Awaitable[None]]
WReqCallable = typing.Callable[[Writer, Request], typing.Awaitable[None]]
NoReqCallable = typing.Callable[[], typing.Awaitable[ASGICallable]]
ReqCallable = typing.Callable[[Request], typing.Awaitable[ASGICallable]]
NoReqRetRespCallable = typing.Callable[[], typing.Awaitable[Response]]
ReqRetRespCallable = typing.Callable[[Request], typing.Awaitable[Response]]


def w_req_adapter(handler: WReqCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        await handler(Writer(send), Request(scope, receive))

    return asgi


def w_adapter(handler: WCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        await handler(Writer(send))

    return asgi


def req_adapter(handler: ReqCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        res = await handler(Request(scope, receive))
        await res(scope, receive, send)

    return asgi


def no_req_adapter(handler: NoReqCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        res = await handler()
        await res(scope, receive, send)

    return asgi


def req_adapter_ret_resp(handler: ReqRetRespCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        res = await handler(Request(scope, receive))
        await send(
            {
                "type": "http.response.start",
                "status": res.status_code,
                "headers": res.headers,
            }
        )
        await send({"type": "http.response.body", "body": res.body})

    return asgi


def no_req_adapter_ret_resp(handler: NoReqRetRespCallable,) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        res = await handler()
        await send(
            {
                "type": "http.response.start",
                "status": res.status_code,
                "headers": res.headers,
            }
        )
        await send({"type": "http.response.body", "body": res.body})

    return asgi


signature_adapters: typing.List[
    typing.Tuple[inspect.Signature, ASGIAdapter]
] = []


def strict_stream_signatures() -> typing.List[
    typing.Tuple[inspect.Signature, ASGIAdapter]
]:
    async def direct(scope: Scope, receive: Receive, send: Send) -> None:
        pass  # pragma: nocover

    async def w(w: Writer) -> None:
        pass  # pragma: nocover

    async def w_req(w: Writer, req: Request) -> None:
        pass  # pragma: nocover

    return [
        (inspect.signature(direct), lambda handler: handler),
        (inspect.signature(w), w_adapter),
        (inspect.signature(w_req), w_req_adapter),
    ]


def strict_resp_signatures() -> typing.List[
    typing.Tuple[inspect.Signature, ASGIAdapter]
]:
    async def req_text(req: Request) -> TextResponse:
        pass  # pragma: nocover

    async def req_bin(req: Request) -> BinaryResponse:
        pass  # pragma: nocover

    async def text() -> TextResponse:
        pass  # pragma: nocover

    async def binary() -> BinaryResponse:
        pass  # pragma: nocover

    async def req_asgi(req: Request) -> ASGICallable:
        pass  # pragma: nocover

    async def asgi() -> ASGICallable:
        pass  # pragma: nocover

    return [
        (inspect.signature(req_text), req_adapter_ret_resp),
        (inspect.signature(req_bin), req_adapter_ret_resp),
        (inspect.signature(text), no_req_adapter_ret_resp),
        (inspect.signature(binary), no_req_adapter_ret_resp),
        (inspect.signature(req_asgi), req_adapter),
        (inspect.signature(asgi), no_req_adapter),
    ]


def strict_signatures() -> typing.List[
    typing.Tuple[inspect.Signature, ASGIAdapter]
]:
    return strict_stream_signatures() + strict_resp_signatures()


signature_adapters.extend(strict_signatures())


@register_asgi_adapter
def handler_adapter_by_signature(
    handler: AnyAsyncCallable,
) -> typing.Optional[ASGICallable]:
    s = inspect.signature(handler)
    for signature, asgi_adapter in signature_adapters:
        if signature == s:
            return asgi_adapter(handler)
    return None
