from slickpy import App, Writer

app = App()


@app.route("/")
async def welcome(w: Writer) -> None:
    await w.end(b"Hello, world!")


# uvicorn --app-dir examples/helloworld app:app
