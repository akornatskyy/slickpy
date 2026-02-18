import inspect
import typing

from slickpy.comp import json_dumps
from slickpy.request import Request
from slickpy.typing import (
    ASGIAdapter,
    ASGICallable,
    Receive,
    Scope,
    Send,
)

NoReqDictCallable = typing.Callable[
    [], typing.Awaitable[typing.Dict]  # type: ignore[type-arg]
]
ReqDictCallable = typing.Callable[
    [Request], typing.Awaitable[typing.Dict]  # type: ignore[type-arg]
]


def no_req_dict_adapter(handler: NoReqDictCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        data = await handler()
        body = json_dumps(
            data,
            ensure_ascii=False,
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (
                        b"content-type",
                        b"application/json; charset=utf-8",
                    ),
                    (b"content-length", str(len(body)).encode("latin-1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    return asgi


def req_dict_adapter(handler: ReqDictCallable) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        data = await handler(Request(scope, receive))
        body = json_dumps(
            data,
            ensure_ascii=False,
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [
                    (
                        b"content-type",
                        b"application/json; charset=utf-8",
                    ),
                    (b"content-length", str(len(body)).encode("latin-1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    return asgi


def json_signatures() -> (
    typing.List[typing.Tuple[inspect.Signature, ASGIAdapter]]
):
    async def no_req_dict() -> typing.Dict:  # type: ignore[type-arg]
        pass  # pragma: nocover

    async def req_dict(req: Request) -> typing.Dict:  # type: ignore[type-arg]
        pass  # pragma: nocover

    return [
        (inspect.signature(no_req_dict), no_req_dict_adapter),
        (inspect.signature(req_dict), req_dict_adapter),
    ]


# responses


def json_response(data: typing.Any, *, status_code: int = 200) -> ASGICallable:
    async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
        body = json_dumps(
            data,
            ensure_ascii=False,
        ).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": [
                    (
                        b"content-type",
                        b"application/json; charset=utf-8",
                    ),
                    (b"content-length", str(len(body)).encode("latin-1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    return asgi
