from typing import *
import asyncio
from .result import *
from .redis_protocol import RedisProtocol
from .redis_task_node import RedisTaskNode
from .redis_session import RedisSession


class RedisServerBase(RedisProtocol):
    IDLE_TIMEOUT = 60
    WORKER_QUEUE = asyncio.Queue()
    ENABLE_AUTH = False
    MAX_DB_COUNT = 1

    def __init__(self, app=None):
        self._http_app = app
        self.host = None
        self.port = None

    @property
    def app(self):
        return self._http_app

    @property
    def password(self):
        return None

    async def handle_stream(self, reader, writer):
        try:
            auth = self.ENABLE_AUTH
            need_auth = True if auth else False
            need_auth_event = asyncio.Event()
            if need_auth:
                need_auth_event.set()
            session = RedisSession()
            session.reader = reader
            session.write = writer
            session.need_auth_event = need_auth_event
            idle_timeout = self.IDLE_TIMEOUT
            while True:
                node_result = await RedisTaskNode.create(session, self)
                if node_result.is_error:
                    raise node_result.error
                if node_result.is_some:
                    node: RedisTaskNode = node_result.unwrap()
                    if node.fa:
                        func, kwargs = node.fa
                        if kwargs:
                            result = await func(**kwargs)
                        else:
                            result = await func()
                        node.result = result
                    write_result = await asyncio.wait_for(node.write_result(session, self),
                                                          timeout=idle_timeout)
        except asyncio.TimeoutError as e:
            return Result(e)
        except Exception as e:
            return Result(e)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception as e:
                pass

    async def serve(self, host='127.0.0.1', port=6379, **kwargs):
        self.host = host
        self.port = port
        server = await asyncio.start_server(self.handle_stream, host, port, **kwargs)
        async with server:
            await server.serve_forever()

    async def get(self, session, key) -> Result[bytes]:
        return Result(NotImplementedError())

    async def getset(self, session, key, value) -> Result:
        return Result(NotImplementedError())

    async def set(self, session, key, value) -> Result:
        return Result(NotImplementedError())

    async def key_type(self, session, key):
        return Result(NotImplementedError())

    async def ping(self, session):
        return Result(NotImplementedError())

    async def info(self, session):
        return Result(NotImplementedError())

    async def auth(self, session, password) -> Result[bool]:
        """
        如果是连接状态问题或者非密码对错的情况下，这里应返回 Result[Exception]
        判断密码正确时，应返回 Result[bool]
        :param session:
        :param password:
        :return:
        """
        return Result(NotImplementedError())

    async def ttl(self, session, key):
        return Result(NotImplementedError())

    async def scan(self, session, pattern):
        return Result(NotImplementedError())

    async def dbsize(self, session):
        return Result(NotImplementedError())

    async def select(self, session, db):
        return Result(NotImplementedError())

    async def config(self, session, get_set, field, value=None):
        return Result(NotImplementedError())


__all__ = ["RedisServerBase", ]
