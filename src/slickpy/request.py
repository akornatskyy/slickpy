import typing
from urllib.parse import parse_qsl

from slickpy.multipart import parse_multipart
from slickpy.typing import (
    FormParams,
    MultipartFiles,
    QueryParams,
    Receive,
    Scope,
)


class Request(object):
    __slots__ = (
        "scope",
        "_body",
        "_cookies",
        "_files",
        "_form",
        "_headers",
        "_query_params",
        "_receive",
    )

    def __init__(self, scope: Scope, receive: Receive):
        self.scope = scope
        self._receive = receive

    @property
    def method(self) -> str:
        return self.scope["method"]  # type: ignore[no-any-return]

    @property
    def route_params(self) -> typing.Mapping[str, str]:
        return self.scope["route_params"]  # type: ignore[no-any-return]

    @property
    def query_params(self) -> QueryParams:
        if not hasattr(self, "_query_params"):
            pairs = parse_qsl(self.scope["query_string"].decode("latin-1"))
            self._query_params = QueryParams(pairs)
        return self._query_params

    @property
    def headers(self) -> typing.Mapping[bytes, bytes]:
        if not hasattr(self, "_headers"):
            self._headers = dict(self.scope["headers"])
        return self._headers

    @property
    def cookies(self) -> typing.Mapping[str, str]:
        if not hasattr(self, "_cookies"):
            cookie = self.headers.get(b"cookie")
            if cookie:
                self._cookies: typing.Mapping[str, str] = dict(
                    [
                        pair.split("=", 1)  # type: ignore[misc]
                        for pair in cookie.decode("latin-1").split("; ")
                    ]
                )
            else:
                self._cookies = {}
        return self._cookies

    async def chunks(self) -> typing.AsyncGenerator[bytes, None]:
        while True:
            message = await self._receive()
            if message["type"] == "http.request":
                chunk = message.get("body")
                if chunk:
                    yield chunk
                if not message.get("more_body"):
                    break
            elif message["type"] == "http.disconnect":
                raise RuntimeError("http disconnect")
            else:
                raise NotImplementedError(
                    f"unexpected message type '{message['type']}' "
                )

    async def body(self) -> bytes:
        if not hasattr(self, "_body"):
            self._body = b"".join([chunk async for chunk in self.chunks()])
        return self._body

    async def form(self) -> FormParams:
        if not hasattr(self, "_form"):
            content_type = self.headers.get(b"content-type", b"")
            if b"/x" in content_type:
                pairs = parse_qsl((await self.body()).decode("utf-8"))
                self._form = FormParams(pairs)
            elif b"/f" in content_type:
                form, files = await parse_multipart(
                    content_type, self.chunks()
                )
                self._form = form
                self._files = files
            else:
                self._form = FormParams([])
        return self._form

    async def files(self) -> MultipartFiles:
        if not hasattr(self, "_files"):
            content_type = self.headers.get(b"content-type", b"")
            if b"/f" in content_type:
                form, files = await parse_multipart(
                    content_type, self.chunks()
                )
                self._form = form
                self._files = files
            else:
                self._files = MultipartFiles([])
        return self._files
