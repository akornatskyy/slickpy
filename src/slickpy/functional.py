import asyncio
import typing
from urllib.parse import unquote, urljoin, urlsplit

from slickpy.typing import ASGICallable, Headers, Message

default_scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.1"},
    "http_version": "1.1",
    "client": ("127.0.0.1", 49327),
    "root_path": "",
}
default_port = {"http": 80, "https": 443}


class Response(object):
    charset = "utf-8"

    def __init__(self) -> None:
        self.status_code: int = 0
        self.headers: typing.Optional[Headers] = None
        self.chunks: typing.List[bytes] = []

    @property
    def body(self) -> bytes:
        return b"".join(self.chunks)

    @property
    def text(self) -> str:
        return self.body.decode(self.charset)


class ASGIClient(object):
    def __init__(
        self, app: ASGICallable, base_url: str = "http://127.0.0.1:8000"
    ) -> None:
        self.app = app
        self.base_url = base_url

    def go(
        self,
        url: str = "/",
        *,
        method: str = "GET",
        headers: typing.Optional[Headers] = None,
    ) -> Response:
        url = urljoin(self.base_url, url)
        scheme, netloc, path, query, _ = urlsplit(url)
        if ":" in netloc:
            host, sport = netloc.split(":", 1)
            port = int(sport)
        else:
            host = netloc
            port = default_port[scheme]
        scope = default_scope.copy()
        scope["scheme"] = scheme
        scope["raw_path"] = urljoin(path, query).encode()
        scope["path"] = unquote(path)
        scope["query_string"] = query.encode()
        scope["method"] = method
        scope["server"] = (host, port)
        if headers is None:
            headers = []
        headers.append((b"host", netloc.encode()))
        headers.append((b"user-agent", b"ASGI Client",))
        scope["headers"] = headers
        res = Response()

        async def receive() -> Message:
            raise NotImplementedError("receive is not implemented")

        async def send(message: Message) -> None:
            if message["type"] == "http.response.start":
                res.status_code = message["status"]
                res.headers = message.get("headers")
            elif message["type"] == "http.response.body":
                # TODO: more_body
                chunk: typing.Optional[bytes] = message.get("body")
                if chunk is not None:
                    res.chunks.append(chunk)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.app(scope, receive, send))

        return res
