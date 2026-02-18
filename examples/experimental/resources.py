from slickpy import App, Writer
from slickpy.experimental.resource import ResourceAdapter
from slickpy.response import JSONResponse

app = App()
resource = ResourceAdapter(app)


@resource("/")
class Resource:
    async def on_get(self, w: Writer) -> None:
        await w.end(b"Hello, world!")


class APIResource:
    async def on_get(self) -> JSONResponse:
        return JSONResponse({"Hello": "World"})

    async def on_post(self, w: Writer) -> None:
        await w.status(201)


api = APIResource()
resource.add("/json", api)

# asgi-cli -v --app-dir examples/experimental resource:main
main = app.asgi()
