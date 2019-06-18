import re
import json
from .redis_server import RedisServer
from .result import Result
from .error import *


class DefaultRedisServer(RedisServer):
    def _db_size(self) -> int:
        app = self.app
        if app is not None:
            return app.sessions_count
        else:
            return 0

    async def get(self, key) -> Result[bytes]:
        app = self.app
        if app is not None and key in app:
            session = app[key]
            status = dict(session_id=key, create_timestamp=session.create_timestamp, current_user=session.current_user)
            return Result(json.dumps(status))
        else:
            return Result(KeyNotFound())

    async def getset(self, key, value) -> Result:
        return Result(NotImplementedError())

    async def set(self, key, value) -> Result:
        app = self.app
        if app is not None and key in app:
            session = app[key]
            await session.send(json.loads(value))
            return Result(True)
        else:
            return Result(KeyNotFound())

    async def key_type(self, key):
        return Result("string")

    async def ping(self):
        return Result("PONG")

    async def info(self):
        info = f"""
        # Server
        porkpepper_version:0.1.0
        tcp_port:{self.port}
        # Keyspace
        db0:keys={self._db_size()},expires=0,avg_ttl=0
        """
        return Result(info)

    async def auth(self, password) -> Result[bool]:
        if self.password is None:
            return Result(NoPasswordError("ERR Client sent AUTH, but no password is set"))
        auth = self.password or ""
        return Result(password == auth.encode("utf8"))

    async def ttl(self, key):
        return Result(-1)

    async def scan(self, pattern):
        app = self.app
        keys = list()
        sessions = app.all_sessions() if app is not None else list()
        for session in sessions:
            if pattern is not None:
                if re.match(pattern, session.session_id):
                    keys.append(session.session_id)
            else:
                keys.append(session.session_id)
        return Result(keys)

    async def dbsize(self):
        return Result(self._db_size())

    async def select(self, db):
        if db == 0:
            return Result(True)
        else:
            return Result(DatabaseNotFound())

    async def config(self, get_set, field, value=None):
        if get_set == b'GET' and field == b'databases':
            return Result([b'databases', b'1'])
        return Result(CommandNotFound())


__all__ = ["DefaultRedisServer", ]
