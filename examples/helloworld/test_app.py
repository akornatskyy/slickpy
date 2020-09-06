import unittest

from slickpy.functional import ASGIClient

from app import main  # noqa: I100, isort: skip


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = ASGIClient(main)

    def test_adapters(self):
        res = self.client.go("/")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text, "Hello, world!")
