import asyncio
import typing
import unittest

from slickpy.multipart import parse_multipart

content_type = b"multipart/form-data; boundary=---123"
body_chunks = [
    b"-----123\r\n",
    b'Content-Disposition: form-data; name="description"\r\n\r\n',
    b"some text\r\n",
    b"-----123\r\n",
    b"Content-Disposition: form-data; ",
    b'name="secret-foo"; filename="foo.txt"\r\n'
    b"Content-Type: text/plain\r\n\r\n"
    b"(content of ",
    b"the uploaded file foo.txt)\r\n",
    b"-----123\r\n",
    b"Content-Disposition: form-data; ",
    b'name="secret-boo"; filename="boo.txt"\r\n'
    b"Content-Type: text/html\r\n\r\n"
    b"(content of ",
    b"the uploaded file boo.txt)\r\n" * 40000,
    b"-----123--",
]


class ParserTestCase(unittest.TestCase):
    def test_parse_multipart(self) -> None:
        async def input(
            chunks: typing.Iterable[bytes],
        ) -> typing.AsyncGenerator[bytes, None]:
            it = chunks.__iter__()
            try:
                while True:
                    yield next(it)
            except StopIteration:
                pass

        loop = asyncio.get_event_loop()
        form, files = loop.run_until_complete(
            parse_multipart(content_type, input(body_chunks))
        )

        self.assertEqual(len(form), 1)
        self.assertEqual(form.description, "some text")
        self.assertEqual(len(files), 2)
        self.assertEqual(
            [
                (name, f.name, f.content_type, f._rolled)
                for name, f in files.items()
            ],
            [
                ("secret-foo", "foo.txt", "text/plain", False),
                ("secret-boo", "boo.txt", "text/html", True),
            ],
        )
        foo = files["secret-foo"]
        self.assertEqual(
            loop.run_until_complete(foo.read()),
            b"(content of the uploaded file foo.txt)",
        )
        boo = files["secret-boo"]
        self.assertEqual(len(loop.run_until_complete(boo.read())), 1120010)

        loop.run_until_complete(files.close())
