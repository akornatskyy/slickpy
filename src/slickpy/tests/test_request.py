import asyncio
import unittest

from slickpy.request import Request
from slickpy.typing import Message


async def noop_receive() -> Message:
    pass  # pragma: nocover


class RequestTestCase(unittest.TestCase):
    def test_method(self) -> None:
        req = Request({"method": "GET"}, noop_receive)
        self.assertEqual(req.method, "GET")

    def test_route_params(self) -> None:
        req = Request({"route_params": {"locale": "uk"}}, noop_receive)
        self.assertEqual(req.route_params, req.scope["route_params"])

    def test_query_params(self) -> None:
        req = Request(
            {
                "query_string": b"msg=hello&"
                b"msg=%D0%BF%D1%80%D0%B8%D0%B2%D1%96%D1%82"
            },
            noop_receive,
        )
        self.assertTrue("msg" in req.query_params)
        self.assertFalse("x" in req.query_params)

    def test_headers(self) -> None:
        req = Request({"headers": [(b"host", b"localhost")]}, noop_receive)
        self.assertEqual(req.headers, {b"host": b"localhost"})
        self.assertEqual(req.headers[b"host"], b"localhost")

    def test_cookies(self) -> None:
        req = Request(
            {"headers": [(b"cookie", b"ID=1234; PREF=abc")]}, noop_receive
        )
        self.assertEqual(req.cookies, {"PREF": "abc", "ID": "1234"})
        req = Request({"headers": []}, noop_receive)
        self.assertEqual(req.cookies, {})

    def test_async_generator(self) -> None:
        async def receive() -> Message:
            return {"type": "http.request", "body": b"Hello, world!"}

        req = Request({}, receive)

        async def read() -> bytes:
            return b"".join([chunk async for chunk in req.chunks()])

        loop = asyncio.get_event_loop()
        body: bytes = loop.run_until_complete(read())

        self.assertEqual(body, b"Hello, world!")

    def test_body(self) -> None:
        receive_chuncks = [b"Hello", b", ", b"world", b"!"]
        it = receive_chuncks.__iter__()

        async def receive() -> Message:
            try:
                return {
                    "type": "http.request",
                    "body": it.__next__(),
                    "more_body": True,
                }
            except StopIteration:
                return {"type": "http.request"}

        req = Request({}, receive)
        loop = asyncio.get_event_loop()
        body = loop.run_until_complete(req.body())

        self.assertEqual(body, b"Hello, world!")

    def test_body_empty(self) -> None:
        async def receive() -> Message:
            return {
                "type": "http.request",
                "body": "",
            }

        req = Request({}, receive)
        loop = asyncio.get_event_loop()
        body = loop.run_until_complete(req.body())

        self.assertEqual(body, b"")

    def test_body_disconnect(self) -> None:
        async def receive() -> Message:
            return {"type": "http.disconnect"}

        req = Request({}, receive)
        loop = asyncio.get_event_loop()
        self.assertRaises(
            RuntimeError, lambda: loop.run_until_complete(req.body())
        )

    def test_body_unexpected_message(self) -> None:
        async def receive() -> Message:
            return {"type": "abc"}

        req = Request({}, receive)
        loop = asyncio.get_event_loop()
        self.assertRaises(
            NotImplementedError, lambda: loop.run_until_complete(req.body())
        )

    def test_form_no_content_type(self) -> None:
        req = Request({"headers": []}, noop_receive,)

        loop = asyncio.get_event_loop()
        form = loop.run_until_complete(req.form())
        self.assertEqual(len(form), 0)
        files = loop.run_until_complete(req.files())
        self.assertEqual(len(files), 0)

    def test_form_unknown_content_type(self) -> None:
        req = Request(
            {"headers": [(b"content-type", b"unknown")]}, noop_receive,
        )

        loop = asyncio.get_event_loop()
        form = loop.run_until_complete(req.form())
        self.assertEqual(len(form), 0)
        files = loop.run_until_complete(req.files())
        self.assertEqual(len(files), 0)

    def test_form_urlencoded(self) -> None:
        async def receive() -> Message:
            return {
                "type": "http.request",
                "body": b"msg=hello",
            }

        req = Request(
            {
                "headers": [
                    (b"content-type", b"application/x-www-form-urlencoded")
                ]
            },
            receive,
        )

        loop = asyncio.get_event_loop()
        form = loop.run_until_complete(req.form())
        self.assertEqual(len(form), 1)
        self.assertEqual(form.msg, "hello")
        files = loop.run_until_complete(req.files())
        self.assertEqual(len(files), 0)

    def test_form_multipart(self) -> None:
        async def receive() -> Message:
            return {
                "type": "http.request",
                "body": b"-----123\r\n"
                b'Content-Disposition: form-data; name="msg"\r\n\r\n'
                b"hello\r\n"
                b"-----123--",
            }

        req = Request(
            {
                "headers": [
                    (b"content-type", b"multipart/form-data; boundary=---123")
                ]
            },
            receive,
        )

        loop = asyncio.get_event_loop()
        form = loop.run_until_complete(req.form())
        self.assertEqual(len(form), 1)
        self.assertEqual(form.msg, "hello")
        files = loop.run_until_complete(req.files())
        self.assertEqual(len(files), 0)

    def test_files_multipart(self) -> None:
        async def receive() -> Message:
            return {
                "type": "http.request",
                "body": b"-----123\r\n"
                b"Content-Disposition: form-data; "
                b'name="secret-foo"; filename="foo.txt"\r\n'
                b"Content-Type: text/plain\r\n\r\n"
                b"(content of "
                b"the uploaded file foo.txt)\r\n"
                b"-----123--",
            }

        req = Request(
            {
                "headers": [
                    (b"content-type", b"multipart/form-data; boundary=---123")
                ]
            },
            receive,
        )

        loop = asyncio.get_event_loop()
        files = loop.run_until_complete(req.files())
        self.assertEqual(len(files), 1)
        form = loop.run_until_complete(req.form())
        self.assertEqual(len(form), 0)
