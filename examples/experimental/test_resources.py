import unittest

from slickpy.comp import json_loads
from slickpy.functional import ASGIClient

from resources import main  # noqa: I100, isort: skip


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = ASGIClient(main)

    def test_get(self):
        res = self.client.go("/")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.text, "Hello, world!")

        res = self.client.go("/", method="POST")

        self.assertEqual(res.status_code, 405)

    def test_json(self):
        res = self.client.go("/json")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(json_loads(res.text), {"Hello": "World"})

        res = self.client.go("/json", method="POST")

        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.text, "")
