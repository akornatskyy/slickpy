from slickpy.typing import Scope


class Request(object):
    __slots__ = ("scope",)

    def __init__(self, scope: Scope):
        self.scope = scope
