import inspect
import typing

from slickpy.application import App
from slickpy.typing import AnyAsyncCallable

HTTP_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE")


class ResourceAdapter(object):

    def __init__(self, app: App):
        self.app = app

    def __call__(
        self,
        pattern: str,
    ) -> typing.Callable[[typing.Type], None]:  # type: ignore[type-arg]
        def decorator(
            handler: AnyAsyncCallable,
        ) -> None:
            self.add(pattern, handler)

        return decorator

    def add(self, pattern: str, handler: AnyAsyncCallable) -> None:
        if inspect.isclass(handler):
            resource = handler()
        else:
            resource = handler
        for m in HTTP_METHODS:
            name = "on_" + m.lower()
            if not hasattr(resource, name):
                continue
            r = getattr(resource, name)
            self.app.add_route(pattern, r, methods=(m,))
