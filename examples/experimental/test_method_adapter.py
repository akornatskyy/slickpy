import unittest

from slickpy.functional import ASGIClient

from method_adapter import main  # noqa: I100, isort: skip


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = ASGIClient(main)

    def test_get(self):
        res = self.client.go("/")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text, "Hello, world!")

    def test_post(self):
        res = self.client.go("/", method="POST")

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.text, "")
