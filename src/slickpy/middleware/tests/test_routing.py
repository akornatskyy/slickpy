import asyncio
import unittest

from slickpy import App
from slickpy.functional import ASGIClient
from slickpy.typing import Message, Receive, Scope, Send


class RoutingMiddlewareTestCase(unittest.TestCase):
    def test_ignores_other_scope_types(self) -> None:
        app = App()

        @app.route("/")
        async def handler() -> None:  # pragma: nocover
            self.fail()

        async def receive() -> Message:  # pragma: nocover
            self.fail()

        async def send(m: Message) -> None:  # pragma: nocover
            self.fail()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(app({"type": "abc"}, receive, send))

    def test_regex_route(self) -> None:
        app = App()

        @app.route(r"^/(?P<user>\w+)/(?P<repo>\w+)$")
        async def handler(scope: Scope, receive: Receive, send: Send) -> None:
            self.assertEqual(
                scope["route_args"], {"repo": "slickpy", "user": "smith"}
            )
            await send(
                {"type": "http.response.start", "status": 200, "headers": []}
            )
            await send(
                {"type": "http.response.body", "body": b"Hello, world!"}
            )

        client = ASGIClient(app)
        res = client.go("/smith/slickpy")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text, "Hello, world!")

    def test_http_method_not_allowed(self) -> None:
        app = App()

        @app.route("/", methods=("POST",))
        async def a() -> None:  # pragma: nocover
            self.fail()

        @app.route(r"^/(?P<locale>en|de|uk)/welcome$", methods=("GET",))
        async def b() -> None:  # pragma: nocover
            self.fail()

        client = ASGIClient(app)
        for pattern in ["/", "/uk/welcome"]:
            res = client.go(pattern, method="PUT")

            self.assertEqual(res.status_code, 405)
            self.assertEqual(res.text, "")

    def test_http_not_found(self) -> None:
        app = App()

        @app.route("/")
        async def a() -> None:  # pragma: nocover
            self.fail()

        @app.route(r"^/(?P<locale>en|de|uk)/welcome$")
        async def b() -> None:  # pragma: nocover
            self.fail()

        client = ASGIClient(app)
        for pattern in ["/x", "/ru/welcome"]:
            res = client.go(pattern)

            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.text, "")
