import re
import json
import asyncio
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

    async def get(self, session, key) -> Result[bytes]:
        app = self.app
        if app is not None and key in app:
            session = app[key]
            status = dict(session_id=key, create_timestamp=session.create_timestamp, current_user=session.current_user)
            return Result(json.dumps(status))
        else:
            return Result(KeyNotFound())

    async def getset(self, session, key, value) -> Result:
        return Result(NotImplementedError())

    @classmethod
    async def send_task(cls, session, message):
        await session.send(message)

    async def set(self, session, key, value) -> Result:
        app = self.app
        if app is not None and key in app:
            session = app[key]
            asyncio.ensure_future(self.send_task(session, json.loads(value)))
            return Result(True)
        else:
            return Result(KeyNotFound())

    async def key_type(self, session, key):
        return Result("string")

    async def ping(self, session):
        return Result("PONG")

    async def info(self, session):
        info = f"""
        # Server
        redis_version:3.0.0
        porkpepper_version:0.1.0
        tcp_port:{self.port}
        # Keyspace
        db0:keys=0,expires=0,avg_ttl=0
        db1:keys={self._db_size()},expires=0,avg_ttl=0
        db2:keys=0,expires=0,avg_ttl=0
        """
        return Result(info)

    async def auth(self, session, password) -> Result[bool]:
        if self.password is None:
            return Result(NoPasswordError("ERR Client sent AUTH, but no password is set"))
        auth = self.password or ""
        return Result(password == auth.encode("utf8"))

    async def ttl(self, session, key):
        return Result(-1)

    def _scan_sessions(self, pattern=None):
        app = self.app
        keys = list()
        sessions = app.all_sessions() if app is not None else list()
        for session in sessions:
            if pattern is not None:
                if re.match(pattern, session.session_id):
                    keys.append(session.session_id)
            else:
                keys.append(session.session_id)
        return keys

    async def scan(self, session, pattern):
        if session.current_db == 0:
            return Result(list())
        if session.current_db == 1:
            keys = self._scan_sessions(pattern)
            return Result(keys)
        if session.current_db == 2:
            return Result(list())
        return Result(list())

    async def dbsize(self, session):
        return Result(self._db_size())

    async def select(self, session, db):
        if 0 <= db < 3:
            session.current_db = db
            return Result(True)
        else:
            return Result(DatabaseNotFound())

    async def config(self, session, get_set, field, value=None):
        if get_set == b'GET' and field == b'databases':
            return Result([b'databases', b'3'])
        return Result(CommandNotFound())


__all__ = ["DefaultRedisServer", ]
