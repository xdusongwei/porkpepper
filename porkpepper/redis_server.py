from typing import *
from jinja2 import Template
from .result import *
from .redis_server_base import RedisServerBase


class RedisServer(RedisServerBase):
    INFO_TEMPLATE = Template(
        """# Server
redis_version:3.0.0
porkpepper_version:0.1.0
porkpepper_mode:{{ porkpepper_mode }}
tcp_port:{{ port }}

# Keyspace
{% for db, info in service_list %}db{{ db }}:keys={{ info["keys"] }},expires=0,avg_ttl=0\r\n{% endfor %}
""", newline_sequence="\r\n")

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


__all__ = ["RedisServer", ]
