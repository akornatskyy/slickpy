import inspect
import typing

from slickpy.request import Request
from slickpy.response import (
    BinaryResponse,
    JSONResponse,
    Response,
    TextResponse,
    Writer,
)
from slickpy.typing import (
    ASGIAdapter,
    ASGICallable,
    AnyAsyncCallable,
    Receive,
    Scope,
    Send,
)

asgi_adapters: typing.List[ASGIAdapter] = []


def register_asgi_adapter(fn: ASGIAdapter) -> None:
    asgi_adapters.insert(0, fn)


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


signature_adapters: typing.List[
    typing.Tuple[inspect.Signature, ASGIAdapter]
] = []


def strict_stream_signatures() -> (
    typing.List[typing.Tuple[inspect.Signature, ASGIAdapter]]
):
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


def strict_req_resp_signatures() -> (
    typing.List[typing.Tuple[inspect.Signature, ASGIAdapter]]
):
    async def req_text(req: Request) -> TextResponse:
        pass  # pragma: nocover

    async def req_bin(req: Request) -> BinaryResponse:
        pass  # pragma: nocover

    async def req_json(req: Request) -> JSONResponse:
        pass  # pragma: nocover

    async def req_asgi(req: Request) -> ASGICallable:
        pass  # pragma: nocover

    return [
        (inspect.signature(req_text), req_adapter),
        (inspect.signature(req_bin), req_adapter),
        (inspect.signature(req_json), req_adapter),
        (inspect.signature(req_asgi), req_adapter),
    ]


def strict_resp_signatures() -> (
    typing.List[typing.Tuple[inspect.Signature, ASGIAdapter]]
):
    async def text() -> TextResponse:
        pass  # pragma: nocover

    async def binary() -> BinaryResponse:
        pass  # pragma: nocover

    async def json() -> JSONResponse:
        pass  # pragma: nocover

    async def asgi() -> ASGICallable:
        pass  # pragma: nocover

    return [
        (inspect.signature(text), no_req_adapter),
        (inspect.signature(binary), no_req_adapter),
        (inspect.signature(json), no_req_adapter),
        (inspect.signature(asgi), no_req_adapter),
    ]


def strict_signatures() -> (
    typing.List[typing.Tuple[inspect.Signature, ASGIAdapter]]
):
    return (
        strict_stream_signatures()
        + strict_req_resp_signatures()
        + strict_resp_signatures()
    )


signature_adapters.extend(strict_signatures())


def handler_adapter_by_signature(
    handler: AnyAsyncCallable,
) -> typing.Optional[ASGICallable]:
    s = inspect.signature(handler)
    for signature, asgi_adapter in signature_adapters:
        if signature == s:
            return asgi_adapter(handler)
    return None


register_asgi_adapter(handler_adapter_by_signature)

__all__ = ("asgi_adapters",)
