import abc
import typing
from base64 import b64encode
from hashlib import sha1

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
        """ Sends an HTTP response header with provided status code.
        """
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


class Response(metaclass=abc.ABCMeta):
    status_code: int
    headers: Headers
    body: bytes


class BinaryResponse(object):
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
        self.headers = headers or []
        self.headers.append(
            (b"content-length", str(len(self.body)).encode("latin-1"))
        )
        self.headers.append((b"content-type", content_type,))

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers,
            }
        )
        await send({"type": "http.response.body", "body": self.body})


class TextResponse(object):
    __slots__ = ("status_code", "headers", "body")

    charset = "utf-8"

    def __init__(
        self,
        content: str,
        status_code: int = 200,
        *,
        headers: typing.Optional[Headers] = None,
        mime_type: str = "text/html",
    ):
        self.status_code = status_code
        self.body = content.encode(self.charset)
        self.headers = headers or []
        self.headers.append(
            (b"content-length", str(len(self.body)).encode("latin-1"))
        )
        self.headers.append(
            (
                b"content-type",
                (mime_type + "; charset=" + self.charset).encode("latin-1"),
            )
        )

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers,
            }
        )
        await send({"type": "http.response.body", "body": self.body})
