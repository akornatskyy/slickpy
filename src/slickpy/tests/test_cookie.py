import unittest

from slickpy.cookie import del_cookie, set_cookie

set_test_cases = (
    (set_cookie("cookie-1", "one"), b"cookie-1=one"),
    (
        set_cookie("cookie-2", "two", max_age=3600),
        b"cookie-2=two; max-age=3600",
    ),
    (
        set_cookie("cookie-3", "three", domain="example.com"),
        b"cookie-3=three; domain=example.com",
    ),
    (
        set_cookie("cookie-3", "three", path="/restricted/"),
        b"cookie-3=three; path=/restricted/",
    ),
    (
        set_cookie("cookie-4", "expiring", expires=1593892940),
        b"cookie-4=expiring; expires=Sat, 04 Jul 2020 20:02:20 GMT",
    ),
    (
        set_cookie("cookie-5", "five", same_site="strict"),
        b"cookie-5=five; samesite=strict",
    ),
    (
        set_cookie("cookie-6", "six", http_only=True),
        b"cookie-6=six; httponly",
    ),
    (
        set_cookie("cookie-7", "seven", secure=True),
        b"cookie-7=seven; secure",
    ),
    (
        set_cookie("cookie-empty-value"),
        b"cookie-empty-value=",
    ),
    (set_cookie("special-1", "a b"), b'special-1="a b"'),
    (set_cookie("special-2", " b"), b'special-2=" b"'),
    (set_cookie("special-3", "a "), b'special-3="a "'),
    (set_cookie("special-4", " "), b'special-4=" "'),
    (set_cookie("special-5", "a,b"), b'special-5="a\\054b"'),
    (set_cookie(""), b"="),
)


del_test_cases = (
    (
        del_cookie("cookie-1"),
        b"cookie-1=; expires=Sat, 01 Jan 2000 00:00:01 GMT",
    ),
    (
        del_cookie("cookie-2", path="/restricted/"),
        b"cookie-2=; path=/restricted/; expires=Sat, 01 Jan 2000 00:00:01 GMT",
    ),
    (
        del_cookie("cookie-3", domain="127.0.0.1"),
        b"cookie-3=; domain=127.0.0.1; expires=Sat, 01 Jan 2000 00:00:01 GMT",
    ),
)


class CookieTestCase(unittest.TestCase):
    def test_cookie(self) -> None:
        for (header, actual), expected in set_test_cases + del_test_cases:
            self.assertEqual(header, b"set-cookie")
            self.assertEqual(actual, expected)
