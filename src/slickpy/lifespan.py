import logging
import typing

from slickpy.typing import LifespanSubscriber, Receive, Scope, Send


class Topic(object):
    def __init__(self) -> None:
        self.subscribers: typing.List[LifespanSubscriber] = []

    def add(self, subscriber: LifespanSubscriber) -> None:
        self.subscribers.append(subscriber)

    async def notify(self) -> None:
        for subscriber in self.subscribers:
            await subscriber()


class Lifespan(object):
    def __init__(self) -> None:
        self.logger = logging.getLogger("slickpy.lifespan")
        self.topics: typing.Dict[str, Topic] = {}

    def add(self, event: str, subscriber: LifespanSubscriber) -> None:
        topic = self.topics.get(event)
        if not topic:
            topic = Topic()
            self.topics[event] = topic
        topic.add(subscriber)

    async def notify(self, event: str) -> None:
        topic = self.topics.get(event)
        if topic:
            await topic.notify()

    async def __call__(
        self, scope: Scope, receive: Receive, send: Send
    ) -> None:
        active = True
        while active:
            message = await receive()
            event = message["type"]
            event_complete = event + ".complete"
            if event == "lifespan.shutdown":
                active = False
            try:
                await self.notify(event)
                await self.notify(event_complete)
                self.logger.info(event_complete)
            except Exception as ex:
                # TODO: logging
                event_failed = event + ".failed"
                await self.notify(event_failed)
                await send({"type": event_failed, "message": str(ex)})
            else:
                await send({"type": event_complete})
