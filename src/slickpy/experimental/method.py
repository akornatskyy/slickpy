import typing

from slickpy.application import App
from slickpy.typing import AnyAsyncCallable


class MethodAdapter(object):

    def __init__(self, app: App):
        self.app = app

    def get(
        self,
        pattern: str,
    ) -> typing.Callable[[typing.Union[AnyAsyncCallable, typing.Any]], None]:
        def decorator(
            handler: typing.Union[AnyAsyncCallable, typing.Any],
        ) -> None:
            self.app.add_route(pattern, handler)

        return decorator

    def post(
        self,
        pattern: str,
    ) -> typing.Callable[[typing.Union[AnyAsyncCallable, typing.Any]], None]:
        def decorator(
            handler: typing.Union[AnyAsyncCallable, typing.Any],
        ) -> None:
            self.app.add_route(pattern, handler, methods=("POST",))

        return decorator
