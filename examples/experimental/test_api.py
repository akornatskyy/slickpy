import unittest

from slickpy.comp import json_loads
from slickpy.functional import ASGIClient

from api import main  # noqa: I100, isort: skip


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.client = ASGIClient(main)

    def test_not_req(self):
        res = self.client.go("/")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(json_loads(res.text), {"Hello": "World"})

    def test_req(self):
        res = self.client.go("/req")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(json_loads(res.text), {"Hello": "World"})

    def test_json_response(self):
        res = self.client.go("/json-response")

        self.assertEqual(res.status_code, 200)
        self.assertEqual(json_loads(res.text), {"Hello": "World"})
