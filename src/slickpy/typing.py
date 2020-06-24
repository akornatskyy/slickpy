import types
import typing

from slickpy.comp import get_running_loop

T = typing.TypeVar("T")

# ASGI
Scope = typing.MutableMapping[str, typing.Any]
Message = typing.MutableMapping[str, typing.Any]
Receive = typing.Callable[[], typing.Awaitable[Message]]
Send = typing.Callable[[Message], typing.Awaitable[None]]
ASGICallable = typing.Callable[[Scope, Receive, Send], typing.Awaitable[None]]

# router
HTTPMethods = typing.Tuple[str, ...]
RouteMatch = typing.Tuple[ASGICallable, HTTPMethods]
ExactMatches = typing.Dict[str, RouteMatch]
RegexMatches = typing.List[typing.Tuple[typing.Pattern[str], RouteMatch]]
RouteResult = typing.Tuple[ExactMatches, RegexMatches]
RouteAdapter = typing.Callable[
    [str, ASGICallable, HTTPMethods], typing.Optional[RouteResult]
]

# response
Headers = typing.List[typing.Tuple[bytes, bytes]]

# lifespan
LifespanSubscriber = typing.Callable[[], typing.Awaitable[None]]

# middleware
Middleware = typing.Callable[[ASGICallable], ASGICallable]

# application
AnyAsyncCallable = typing.Callable[..., typing.Awaitable[typing.Any]]
ASGIAdapter = typing.Callable[
    [AnyAsyncCallable], typing.Optional[ASGICallable]
]


# abstractions


class ItemsView(typing.ItemsView[str, T]):
    __slots__ = ("_mapping",)

    def __init__(self, mapping: typing.Mapping[str, typing.List[T]]) -> None:
        self._mapping = mapping

    def __contains__(  # type: ignore[override]
        self, item: typing.Tuple[str, T]
    ) -> bool:
        key, value = item
        mapping = self._mapping
        if key in mapping:
            for v in mapping[key]:
                if v is value or v == value:
                    return True
        return False

    def __iter__(self) -> typing.Iterator[typing.Tuple[str, T]]:
        mapping = self._mapping
        for key in mapping:
            for value in mapping[key]:
                yield key, value


class ValuesView(typing.ValuesView[T]):
    __slots__ = ("_mapping",)

    def __init__(self, mapping: typing.Mapping[str, typing.List[T]]) -> None:
        self._mapping = mapping

    def __contains__(  # type: ignore[override]
        self, value: T
    ) -> bool:
        mapping = self._mapping
        for key in mapping:
            for v in mapping[key]:
                if v is value or v == value:
                    return True
        return False

    def __iter__(self) -> typing.Iterator[T]:
        mapping = self._mapping
        for key in mapping:
            for value in mapping[key]:
                yield value


class Params(typing.Mapping[str, T]):
    __slots__ = ("_mapping",)

    def __init__(self, pairs: typing.List[typing.Tuple[str, T]]) -> None:
        mapping: typing.MutableMapping[str, typing.List[T]] = {}
        for key, value in pairs:
            if key in mapping:
                mapping[key].append(value)
            else:
                mapping[key] = [value]
        self._mapping = mapping

    def __getitem__(self, key: str) -> T:
        return self._mapping[key][-1]

    def __getattr__(self, key: str) -> T:
        if key in self._mapping:
            return self._mapping[key][-1]
        raise AttributeError(key)

    def __len__(self) -> int:
        return len(self._mapping)

    def __iter__(self) -> typing.Iterator[str]:
        return self._mapping.__iter__()

    def __contains__(self, key: typing.Any) -> bool:
        return key in self._mapping

    def items(self) -> typing.AbstractSet[typing.Tuple[str, T]]:
        return ItemsView(self._mapping)

    def values(self) -> typing.ValuesView[T]:
        return ValuesView(self._mapping)

    def get(  # type: ignore[override]
        self, key: str, default: typing.Optional[T] = None
    ) -> typing.Optional[T]:
        if key in self._mapping:
            return self._mapping[key][-1]
        return default

    def getlist(self, key: str) -> typing.List[T]:
        if key in self._mapping:
            return self._mapping[key]
        return []


# request
QueryParams = Params[str]
FormParams = Params[str]

# multipart

TMF = typing.TypeVar("TMF", bound="MultipartFile")


class MultipartFile(object):
    def __init__(
        self,
        name: str,
        content_type: str,
        rolled: bool,
        file: typing.IO[bytes],
    ) -> None:
        self.name = name
        self.content_type = content_type
        self._rolled = rolled
        self._file = file

    async def __aenter__(self: TMF) -> TMF:
        if self._file.closed:
            raise ValueError("Cannot enter context with closed file")
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()

    async def read(self, size: int = -1) -> bytes:
        if self._rolled:
            return await get_running_loop().run_in_executor(
                None, self._file.read, size
            )
        return self._file.read(size)

    async def close(self) -> None:
        if self._rolled:
            await get_running_loop().run_in_executor(None, self._file.close)
        else:
            self._file.close()


TMFS = typing.TypeVar("TMFS", bound="MultipartFiles")


class MultipartFiles(Params[MultipartFile]):
    async def __aenter__(self: TMFS) -> TMFS:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]],
        exc_value: typing.Optional[BaseException],
        traceback: typing.Optional[types.TracebackType],
    ) -> None:
        await self.close()

    async def close(self) -> None:
        for f in self.values():
            await f.close()
