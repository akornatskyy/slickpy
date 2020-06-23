import typing
from urllib.parse import parse_qsl

from slickpy.typing import Receive, Scope


class QueryParams(typing.Mapping[str, str]):
    __slots__ = ("_d",)

    def __init__(self, qs: bytes) -> None:
        qsl = parse_qsl(qs.decode("latin-1"))
        d: typing.MutableMapping[str, typing.List[str]] = {}
        for key, value in qsl:
            if key in d:
                d[key].append(value)
            else:
                d[key] = [value]
        self._d = d

    def __getitem__(self, key: str) -> str:
        if key in self._d:
            return self._d[key][-1]
        return ""

    def __len__(self) -> int:
        return len(self._d)

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self._d.keys())

    def __contains__(self, key: typing.Any) -> bool:
        return key in self._d

    def get(self, key: typing.Any, default: typing.Any = None) -> typing.Any:
        if key in self._d:
            return self._d[key][-1]
        return default

    def getlist(self, key: str) -> typing.List[str]:
        if key in self._d:
            return self._d[key]
        return []


class Request(object):
    __slots__ = (
        "scope",
        "_receive",
        "_headers",
        "_query_params",
        "_cookies",
        "_body",
    )

    def __init__(self, scope: Scope, receive: Receive):
        self.scope = scope
        self._receive = receive

    @property
    def method(self) -> str:
        return self.scope["method"]  # type: ignore

    @property
    def route_params(self) -> typing.Mapping[str, str]:
        return self.scope["route_params"]  # type: ignore

    @property
    def query_params(self) -> QueryParams:
        if not hasattr(self, "_query_params"):
            self._query_params = QueryParams(self.scope["query_string"])
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
                        pair.split("=", 1)  # type: ignore
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
