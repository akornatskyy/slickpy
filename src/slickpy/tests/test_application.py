import asyncio
import typing
import unittest

from slickpy import App, Request, Writer
from slickpy.functional import ASGIClient
from slickpy.response import BinaryResponse, TextResponse
from slickpy.typing import ASGICallable, Message, Receive, Scope, Send

app = App()

# region: lifespan events
events = []


@app.on("lifespan.startup")
async def startup() -> None:
    events.append("lifespan.startup")


@app.on("lifespan.startup.complete")
async def startup_complete() -> None:
    events.append("lifespan.startup.complete")


@app.on("lifespan.shutdown")
async def shutdown() -> None:
    events.append("lifespan.shutdown")


@app.on("lifespan.shutdown.complete")
async def shutdown_complete() -> None:
    events.append("lifespan.shutdown.complete")


# region: routes


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
async def no_request() -> BinaryResponse:
    return BinaryResponse(b"Hello, world!")


@app.route("/with-request")
async def with_request(req: Request) -> TextResponse:
    return TextResponse("Hello, world!")


@app.route("/stream")
async def stream(w: Writer) -> None:
    await w.write(b"Hello")
    await w.write(b", ")
    await w.write(b"world")
    await w.end(b"!")


@app.route("/status")
async def status(w: Writer) -> None:
    await w.status(201)
    await w.end()


class AppTestCase(unittest.TestCase):
    def test_adapters(self) -> None:
        client = ASGIClient(app)
        for path in [
            "/asgi",
            "/writer",
            "/writer-request",
            "/no-request",
            "https://localhost/with-request",
            "/stream",
        ]:
            res = client.go(path)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.text, "Hello, world!")

    def test_status(self) -> None:
        client = ASGIClient(app)
        res = client.go("/status")

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.text, "")

    def test_on_subscription(self) -> None:
        receive_events = ["lifespan.startup", "lifespan.shutdown"]
        it = receive_events.__iter__()

        async def receive() -> Message:
            return {"type": it.__next__()}

        sent_events = []

        async def send(m: Message) -> None:
            sent_events.append(m["type"])

        loop = asyncio.get_event_loop()
        loop.run_until_complete(app({"type": "lifespan"}, receive, send))

        self.assertEqual(
            events,
            [
                "lifespan.startup",
                "lifespan.startup.complete",
                "lifespan.shutdown",
                "lifespan.shutdown.complete",
            ],
        )
        self.assertEqual(
            sent_events,
            ["lifespan.startup.complete", "lifespan.shutdown.complete",],
        )

    def test_middleware(self) -> None:
        main = App()
        calls = []

        @main.middleware
        def my_middleware(following: ASGICallable) -> ASGICallable:
            calls.append("init")

            async def w(scope: Scope, receive: Receive, send: Send) -> None:
                calls.append("before")
                await following(scope, receive, send)
                calls.append("after")

            return w

        @main.route("/")
        async def root() -> TextResponse:
            return TextResponse("root")

        client = ASGIClient(main)
        res = client.go()

        self.assertEqual(res.text, "root")
        self.assertEqual(calls, ["init", "before", "after"])

    def test_unknown_asgi_adapter(self) -> None:
        async def root(f: float) -> None:  # pragma: nocover
            pass

        main = App()
        self.assertRaises(AssertionError, lambda: main.route("/")(root))

        not_callable = typing.cast(
            typing.Callable[[], typing.Awaitable[None]], 1
        )
        self.assertRaises(
            AssertionError, lambda: main.route("/")(not_callable)
        )

    def test_lifespan_event_fails(self) -> None:
        main = App()
        dispatched_events = []
        sent_events = []

        @main.on("lifespan.shutdown")
        async def shutdown() -> None:
            dispatched_events.append("shutdown")
            raise ValueError()

        @main.on("lifespan.shutdown.failed")
        async def failed() -> None:
            dispatched_events.append("shutdown.failed")

        @main.on("lifespan.shutdown.complete")
        async def complete() -> None:  # pragma: nocover
            self.fail()

        async def receive() -> Message:
            return {"type": "lifespan.shutdown"}

        async def send(m: Message) -> None:
            sent_events.append(m["type"])

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main({"type": "lifespan"}, receive, send))

        self.assertEqual(dispatched_events, ["shutdown", "shutdown.failed"])
        self.assertEqual(sent_events, ["lifespan.shutdown.failed"])
