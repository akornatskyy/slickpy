import typing

from slickpy.adapters import asgi_adapters
from slickpy.lifespan import Lifespan
from slickpy.middleware.routing import RoutingMiddleware
from slickpy.router import Router
from slickpy.typing import (
    ASGICallable,
    AnyAsyncCallable,
    HTTPMethods,
    LifespanSubscriber,
    Middleware,
)


class App(object):
    def __init__(self) -> None:
        self.router = Router()
        self.lifespan = Lifespan()
        self.entry: ASGICallable = RoutingMiddleware(
            self.router, self.lifespan
        )

    def middleware(self, m: Middleware) -> None:
        self.entry = m(self.entry)

    def route(
        self,
        pattern: str,
        *,
        methods: HTTPMethods = ("GET", "HEAD"),
    ) -> typing.Callable[[AnyAsyncCallable], None]:
        def decorator(
            handler: AnyAsyncCallable,
        ) -> None:
            self.add_route(pattern, handler, methods=methods)

        return decorator

    def add_route(
        self,
        pattern: str,
        handler: AnyAsyncCallable,
        *,
        methods: HTTPMethods = ("GET", "HEAD"),
    ) -> None:
        if callable(handler):
            for asgi_adapter in asgi_adapters:
                asgi_callable = asgi_adapter(handler)
                if asgi_callable:
                    self.router.add(pattern, asgi_callable, methods=methods)
                    break
            else:
                raise AssertionError(
                    f"unable to find asgi adapter for pattern '{pattern}'"
                )

    def on(self, event: str) -> typing.Callable[[LifespanSubscriber], None]:
        def decorator(subscriber: LifespanSubscriber) -> None:
            self.lifespan.add(event, subscriber)

        return decorator

    def asgi(self) -> ASGICallable:
        return self.entry
