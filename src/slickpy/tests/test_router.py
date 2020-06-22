import unittest

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
            exact_matches, regex_matches = route(pattern, handler)
            self.assertEqual(exact_matches, {})
            self.assertEqual(len(regex_matches), 1)
            self.assertEqual(len(regex_matches[0]), 2)
            self.assertEqual(regex_matches[0][1], (handler, ("GET", "HEAD")))
