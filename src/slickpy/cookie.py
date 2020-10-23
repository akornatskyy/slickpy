import typing
from http.cookies import _quote  # type: ignore[attr-defined]
from time import gmtime, strftime

_join = "".join


def set_cookie(  # noqa: CFQ002
    name: str,
    value: str = "",
    path: str = "",
    expires: float = -1,
    max_age: int = 0,
    domain: str = "",
    secure: bool = False,
    http_only: bool = False,
    same_site: str = "",
) -> typing.Tuple[bytes, bytes]:
    directives: typing.List[str] = []
    append = directives.append
    append(name + "=")
    if value:
        append(_quote(value))
    if path:
        append("; path=" + path)
    if domain:
        append("; domain=" + domain)
    if expires >= 0:
        append(
            "; expires="
            + strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime(expires))
        )
    if max_age:
        append("; max-age=" + str(max_age))
    if same_site:
        append("; samesite=" + same_site)
    if http_only:
        append("; httponly")
    if secure:
        append("; secure")
    return (b"set-cookie", _join(directives).encode("latin-1"))


def del_cookie(
    name: str, path: str = "", domain: str = ""
) -> typing.Tuple[bytes, bytes]:
    directives: typing.List[str] = []
    append = directives.append
    append(name + "=")
    if path:
        append("; path=" + path)
    if domain:
        append("; domain=" + domain)
    append("; expires=Sat, 01 Jan 2000 00:00:01 GMT")
    return (b"set-cookie", _join(directives).encode("latin-1"))
