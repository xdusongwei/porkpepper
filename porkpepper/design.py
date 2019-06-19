from .node import PorkPepperNode


class WebsocketNode(PorkPepperNode):
    pass


class RedisServiceNode(PorkPepperNode):
    pass


__all__ = ["WebsocketNode", "RedisServiceNode", ]
