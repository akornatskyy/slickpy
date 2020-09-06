import typing
from base64 import b64encode
from hashlib import sha1

from slickpy.comp import ujson_dumps
from slickpy.typing import Headers, Receive, Scope, Send


def make_etag(body: bytes) -> bytes:
    length = len(body)
    if length == 0:
        return b'"0-2jmj7l5rSw0yVb/vlWAYkK/YBwk"'
    h = sha1()
    h.update(body)
    code = b64encode(h.digest())[:27].decode("latin1")
    return f'W/"{length:x}-{code}"'.encode("latin1")


class Writer(object):
    __slots__ = ("_send", "headers", "headersSent")

    def __init__(self, send: Send):
        self._send = send
        self.headers: Headers = []
        self.headersSent = False

    async def status(self, code: int) -> None:
        """Sends an HTTP response header with provided status code."""
        self.headersSent = True
        await self._send(
            {
                "type": "http.response.start",
                "status": code,
                "headers": self.headers,
            }
        )

    async def write(self, chunk: bytes) -> None:
        if not self.headersSent:
            self.headersSent = True
            await self._send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": self.headers,
                }
            )
        await self._send(
            {"type": "http.response.body", "body": chunk, "more_body": True}
        )

    async def end(self, chunk: bytes = b"") -> None:
        if not self.headersSent:
            await self._send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": self.headers,
                }
            )
        await self._send({"type": "http.response.body", "body": chunk})


class Response(object):
    __slots__ = ("status_code", "headers", "body")
    status_code: int
    headers: Headers
    body: bytes

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        status_code = self.status_code
        headers = self.headers
        body = self.body
        method = scope["method"]
        no_body = method == "HEAD"
        if status_code == 200 and (no_body or method == "GET"):
            etag = make_etag(body)
            for name, value in scope["headers"]:
                if name == b"if-none-match":
                    if etag in value:
                        status_code = 304
                        no_body = True
                    break
            headers.append(
                (b"etag", etag),
            )
        await send(
            {
                "type": "http.response.start",
                "status": status_code,
                "headers": headers,
            }
        )
        if no_body:
            await send({"type": "http.response.body"})
        else:
            await send({"type": "http.response.body", "body": body})


class BinaryResponse(Response):
    __slots__ = ("status_code", "headers", "body")

    def __init__(
        self,
        body: bytes,
        status_code: int = 200,
        *,
        headers: typing.Optional[Headers] = None,
        content_type: bytes = b"application/octet-stream",
    ):
        self.status_code = status_code
        self.body = body
        self.headers = headers = headers or []
        headers.append(
            (b"content-length", str(len(self.body)).encode("latin-1"))
        )
        headers.append(
            (
                b"content-type",
                content_type,
            )
        )


class TextResponse(Response):
    __slots__ = ("status_code", "headers", "body")

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        *,
        headers: typing.Optional[Headers] = None,
        mime_type: str = "text/html",
        charset: str = "utf-8",
    ):
        self.status_code = status_code
        self.body = content.encode(charset)
        self.headers = headers = headers or []
        headers.append(
            (b"content-length", str(len(self.body)).encode("latin-1"))
        )
        headers.append(
            (
                b"content-type",
                (mime_type + "; charset=" + charset).encode("latin-1"),
            )
        )


class JSONResponse(Response):
    __slots__ = ("status_code", "headers", "body")

    def __init__(
        self,
        obj: typing.Any,
        status_code: int = 200,
        *,
        headers: typing.Optional[Headers] = None,
    ):
        self.status_code = status_code
        # https://github.com/ultrajson/ultrajson#ensure_ascii
        body = ujson_dumps(obj, False).encode("utf-8")
        self.body = body
        self.headers = headers = headers or []
        headers.append((b"content-length", str(len(body)).encode("latin-1")))
        headers.append(
            (
                b"content-type",
                b"application/json; charset=utf-8",
            )
        )
