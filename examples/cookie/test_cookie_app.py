import unittest

from slickpy.functional import ASGIClient

from cookie_app import main  # noqa: I100, isort: skip


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = ASGIClient(main)

    def test_with_writer(self):
        res = self.client.go("/writer")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers, [(b"set-cookie", b"cookie-1=abc")])
        self.assertEqual(res.text, "Hello, world!")

        res = self.client.go("/writer", method="DELETE")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers,
            [
                (
                    b"set-cookie",
                    b"cookie-1=; expires=Sat, 01 Jan 2000 00:00:01 GMT",
                )
            ],
        )
        self.assertEqual(res.text, "Hello, world!")

    def test_with_response(self):
        res = self.client.go("/response")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers,
            [
                (b"set-cookie", b"cookie-1=abc"),
                (b"content-length", b"13"),
                (b"content-type", b"text/html; charset=utf-8"),
                (b"etag", b'W/"d-lDpwLQbzRZmu4fjajvn3KWAx1pk"'),
            ],
        )
        self.assertEqual(res.text, "Hello, world!")

        res = self.client.go("/response", method="DELETE")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(
            res.headers,
            [
                (b"content-length", b"13"),
                (b"content-type", b"text/html; charset=utf-8"),
                (
                    b"set-cookie",
                    b"cookie-1=; expires=Sat, 01 Jan 2000 00:00:01 GMT",
                ),
            ],
        )
        self.assertEqual(res.text, "Hello, world!")
