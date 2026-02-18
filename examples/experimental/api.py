import typing

from slickpy.adapters import signature_adapters
from slickpy.application import App
from slickpy.experimental.json import json_response, json_signatures
from slickpy.experimental.method import MethodAdapter
from slickpy.request import Request
from slickpy.typing import ASGICallable

signature_adapters.extend(json_signatures())

app = App()
http = MethodAdapter(app)


@http.get("/")
async def hi() -> typing.Dict:
    return {"Hello": "World"}


@http.get("/req")
async def hi_req(req: Request) -> typing.Dict:
    return {"Hello": "World"}


@http.get("/json-response")
async def hi_with_json_response() -> ASGICallable:
    return json_response({"Hello": "World"})


# asgi-cli -v --app-dir examples/experimental api:main
main = app.asgi()
