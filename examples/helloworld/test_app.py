import unittest

from slickpy.functional import ASGIClient

from app import app  # noqa: I100


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = ASGIClient(app)

    def test_adapters(self):
        res = self.client.go("/")

        self.assertEquals(res.status_code, 200)
        self.assertEquals(res.text, "Hello, world!")
