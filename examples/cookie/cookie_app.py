from slickpy import App, Request, Writer
from slickpy.cookie import del_cookie, set_cookie
from slickpy.response import TextResponse

app = App()


@app.route("/writer", methods=("GET", "DELETE"))
async def writer_example(w: Writer, req: Request) -> None:
    if req.method == "DELETE":
        w.headers.append(del_cookie("cookie-1"))
    else:
        w.headers.append(set_cookie("cookie-1", "abc"))
    await w.end(b"Hello, world!")


@app.route("/response", methods=("GET", "DELETE"))
async def response_example(req: Request) -> TextResponse:
    if req.method == "DELETE":
        res = TextResponse("Hello, world!")
        res.headers.append(del_cookie("cookie-1"))
        return res

    return TextResponse(
        "Hello, world!", headers=[set_cookie("cookie-1", "abc")]
    )


main = app.asgi()
