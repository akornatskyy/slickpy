from slickpy import App, Writer
from slickpy.experimental.method import MethodAdapter

app = App()
http = MethodAdapter(app)


@http.get("/")
async def hi(w: Writer) -> None:
    await w.end(b"Hello, world!")


@http.post("/")
async def create(w: Writer) -> None:
    await w.status(201)
    await w.end()


# asgi-cli -v --app-dir examples/experimental method_adapter:main
main = app.asgi()
