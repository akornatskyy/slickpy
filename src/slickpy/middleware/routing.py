from slickpy.router import Router
from slickpy.typing import ASGICallable, Receive, Scope, Send


class RoutingMiddleware(object):
    def __init__(self, router: Router, lifespan: ASGICallable):
        self.exact_matches = router.exact_matches
        self.regex_matches = router.regex_matches
        self.lifespan = lifespan

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
            return
        path = scope["path"]
        route = self.exact_matches.get(path)
        if route:
            handler, http_verbs = route
            if scope["method"] in http_verbs:
                await handler(scope, receive, send)
            else:
                await handle_http_status(send, 405)
            return
        for regex, route in self.regex_matches:
            m = regex.match(path)
            if m:
                handler, http_verbs = route
                if scope["method"] in http_verbs:
                    scope["route_params"] = m.groupdict()
                    await handler(scope, receive, send)
                else:
                    await handle_http_status(send, 405)
                return
        await handle_http_status(send, 404)


async def handle_http_status(send: Send, code: int) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": code,
            "headers": [(b"content-length", b"0")],
        }
    )
    await send({"type": "http.response.body"})
