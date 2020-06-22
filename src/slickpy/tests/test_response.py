import unittest

from slickpy.response import make_etag


class ETagTestCase(unittest.TestCase):
    def test_etag(self) -> None:
        for body, expected in [
            (b"", b'"0-2jmj7l5rSw0yVb/vlWAYkK/YBwk"'),
            (b"Hello, world!", b'W/"d-lDpwLQbzRZmu4fjajvn3KWAx1pk"'),
        ]:
            actual = make_etag(body)
            self.assertEqual(actual, expected)
