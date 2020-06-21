import unittest

from slickpy import App, Request, Writer
from slickpy.functional import ASGIClient
from slickpy.response import TextResponse
from slickpy.typing import Receive, Scope, Send

app = App()


@app.route("/asgi")
async def asgi(scope: Scope, receive: Receive, send: Send) -> None:
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"Hello, world!"})


@app.route("/writer")
async def writer(w: Writer) -> None:
    await w.end(b"Hello, world!")


@app.route("/writer-request")
async def writer_request(w: Writer, req: Request) -> None:
    await w.end(b"Hello, world!")


@app.route("/no-request")
async def no_request() -> TextResponse:
    return TextResponse("Hello, world!")


@app.route("/with-request")
async def with_request(req: Request) -> TextResponse:
    return TextResponse("Hello, world!")


class AppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = ASGIClient(app)

    def test_adapters(self) -> None:
        for path in [
            "/asgi",
            "/writer",
            "/writer-request",
            "/no-request",
            "/with-request",
        ]:
            res = self.client.go(path)

            assert res.status_code == 200
            assert res.text == "Hello, world!"
