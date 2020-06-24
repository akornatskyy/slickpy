import asyncio
import io
import unittest

from slickpy.typing import MultipartFile, MultipartFiles, Params


class ParamsTestCase(unittest.TestCase):
    def test_getitem(self) -> None:
        p = Params([("msg", "hi")])
        self.assertEqual(p["msg"], "hi")

    def test_getitem_returns_last(self) -> None:
        p = Params([("msg", "hello"), ("msg", "hi")])
        self.assertEqual(p["msg"], "hi")

    def test_getitem_raises_key_error(self) -> None:
        p: Params[str] = Params([])
        self.assertRaises(KeyError, lambda: p["msg"])

    def test_getattr(self) -> None:
        p = Params([("msg", "hi")])
        self.assertEqual(p.msg, "hi")

    def test_getattr_returns_last(self) -> None:
        p = Params([("msg", "hello"), ("msg", "hi")])
        self.assertEqual(p.msg, "hi")

    def test_getattr_raises_attribute_error(self) -> None:
        p: Params[str] = Params([])
        self.assertRaises(AttributeError, lambda: p.msg)

    def test_len(self) -> None:
        p: Params[str] = Params([])
        self.assertEqual(len(p), 0)
        p = Params([("msg", "hello")])
        self.assertEqual(len(p), 1)
        p = Params([("msg", "hello"), ("msg", "hi")])
        self.assertEqual(len(p), 1)

    def test_iter(self) -> None:
        p: Params[str] = Params([])
        self.assertEqual(list(p), [])
        p = Params([("msg", "hello")])
        self.assertEqual(list(p), ["msg"])
        p = Params([("msg", "hello"), ("msg", "hi")])
        self.assertEqual(list(p), ["msg"])

    def test_contains(self) -> None:
        p: Params[str] = Params([])
        self.assertFalse("msg" in p)
        p = Params([("msg", "hello")])
        self.assertTrue("msg" in p)
        self.assertFalse("x" in p)

    def test_items(self) -> None:
        p: Params[str] = Params([])
        self.assertEqual(list(p.items()), [])
        p = Params([("msg", "hello"), ("msg", "hi")])
        self.assertFalse(("x", "hi") in p.items())
        self.assertFalse(("msg", "") in p.items())
        self.assertTrue(("msg", "hello") in p.items())
        self.assertTrue(("msg", "hi") in p.items())

    def test_values(self) -> None:
        p: Params[str] = Params([])
        self.assertFalse("hi" in p.values())
        self.assertEqual(list(p.values()), [])
        p = Params([("msg", "hello"), ("msg", "hi")])
        self.assertEqual(list(p.values()), ["hello", "hi"])
        self.assertTrue("hi" in p.values())

    def test_get(self) -> None:
        p: Params[str] = Params([])
        self.assertEqual(p.get("msg"), None)
        self.assertEqual(p.get("x", "default"), "default")
        p = Params([("msg", "hello"), ("msg", "hi")])
        self.assertEqual(p.get("msg"), "hi")

    def test_getlist(self) -> None:
        p: Params[str] = Params([])
        self.assertEqual(p.getlist("msg"), [])
        p = Params([("msg", "hello"), ("msg", "hi")])
        self.assertEqual(p.getlist("msg"), ["hello", "hi"])


class MultipartFileTestCase(unittest.TestCase):
    def test_context_manager(self) -> None:
        async def f() -> bytes:
            async with MultipartFile("", "", False, io.BytesIO(b"hi")) as f:
                return await f.read()

        loop = asyncio.get_event_loop()
        self.assertEqual(loop.run_until_complete(f()), b"hi")

    def test_context_manager_raises_value_error(self) -> None:
        async def f() -> None:
            f = MultipartFile("", "", False, io.BytesIO(b"hi"))
            async with f:
                await f.read()
            async with f:
                pass  # pragma: nocover

        loop = asyncio.get_event_loop()
        self.assertRaises(ValueError, lambda: loop.run_until_complete(f()))


class MultipartFilesTestCase(unittest.TestCase):
    def test_context_manager(self) -> None:
        async def f() -> None:
            async with MultipartFiles([]) as files:
                await files.close()

        loop = asyncio.get_event_loop()
        loop.run_until_complete(f())
