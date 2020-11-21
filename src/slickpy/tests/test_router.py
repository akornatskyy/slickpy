import unittest

from slickpy import App, Request
from slickpy.functional import ASGIClient
from slickpy.response import TextResponse
from slickpy.router import route
from slickpy.typing import Receive, Scope, Send


class RouterTestCase(unittest.TestCase):
    def test_regex_route(self) -> None:
        async def handler(scope: Scope, receive: Receive, send: Send) -> None:
            pass  # pragma: nocover

        for pattern in [
            r"^/(?P<user>\w+)/(?P<repo>\w+)$",
            r"^/(?P<locale>en|de|uk)/welcome$",
        ]:
            exact_matches, regex_matches = route(pattern)
            self.assertEqual(exact_matches, [])
            self.assertEqual(len(regex_matches), 1)

    def test_http_methods(self) -> None:
        for method in ["GET", "POST", "PUT", "DELETE"]:
            res = client.go(method=method)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.text, method)
            res = client.go("/uk/welcome", method=method)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.text, method)
        for method in ["PATCH", "OPTIONS"]:
            res = client.go(method=method)
            self.assertEqual(res.status_code, 405)
            res = client.go("/uk/welcome", method=method)
            self.assertEqual(res.status_code, 405)

    def test_route_head_method(self) -> None:
        res = client.go(method="HEAD")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text, "")
        res = client.go("/uk/welcome", method="HEAD")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text, "")

    def test_route_not_found(self) -> None:
        for method in ["GET", "POST", "PUT", "DELETE"]:
            res = client.go("/does-not-exist", method=method)
            self.assertEqual(res.status_code, 404)
            self.assertEqual(res.text, "")


app = App()
client = ASGIClient(app.asgi())


@app.route("/")
async def root(req: Request) -> TextResponse:
    return TextResponse(req.method)


@app.route("/", methods=("POST", "PUT", "DELETE"))
async def other_methods(req: Request) -> TextResponse:
    return TextResponse(req.method)


@app.route(r"^/(?P<locale>en|de|uk)/welcome$")
async def welcome(req: Request) -> TextResponse:
    return TextResponse(req.method)


@app.route(
    r"^/(?P<locale>en|de|uk)/welcome$",
    methods=("POST", "PUT", "DELETE"),
)
async def welcome_methods(req: Request) -> TextResponse:
    return TextResponse(req.method)
