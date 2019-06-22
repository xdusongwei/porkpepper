import json
import asyncio
import pytest
import aioredis
from porkpepper.design import *


class ServiceAtZero:
    @classmethod
    @service("add", output=True, description="add function")
    async def add(cls, message):
        x = message.get("x", 0)
        y = message.get("y", 0)
        return dict(result=x+y)


class ServiceAtOne:
    @classmethod
    @service("plus", output=True, meta=dict(info="test_info"))
    async def plus(cls, message):
        x = message.get("x", 0)
        y = message.get("y", 0)
        return dict(result=x + y)


@pytest.mark.asyncio
async def test_service():
    node = RedisServiceNode()
    await node.start(service_map={0: ServiceAtZero, 1: ServiceAtOne}, redis_host="127.0.0.1", redis_port=6666)

    # db 0
    conn = await aioredis.create_redis('redis://127.0.0.1:6666/0')
    result = await conn.getset("add", json.dumps(dict(x=1, y=2)))
    result = json.loads(result)
    assert result == dict(result=3)
    no_exists_command = await conn.get("xyz")
    assert no_exists_command is None
    add_command = await conn.get("add")
    assert add_command
    add_command = json.loads(add_command)
    assert add_command["key"] == "add"
    assert isinstance(add_command["output"], bool) and add_command["output"]
    assert add_command["description"] == "add function"
    dbsize = await conn.dbsize()
    assert dbsize == 1
    await common_command_check(conn)
    conn.close()

    # db 1
    conn = await aioredis.create_redis('redis://127.0.0.1:6666/1')
    result = await conn.getset("plus", json.dumps(dict(x=5, y=16)))
    result = json.loads(result)
    assert result == dict(result=21)
    no_exists_command = await conn.get("xyz")
    assert no_exists_command is None
    plus_command = await conn.get("plus")
    assert plus_command
    plus_command = json.loads(plus_command)
    assert plus_command["key"] == "plus"
    assert isinstance(plus_command["output"], bool) and plus_command["output"]
    assert plus_command["description"] is None
    assert plus_command["meta"] == dict(info="test_info")
    dbsize = await conn.dbsize()
    assert dbsize == 1
    await common_command_check(conn)
    conn.close()

    await node.stop()

    async with await node.start(service_map={0: ServiceAtZero}, redis_host="127.0.0.1", redis_port=6666):
        conn = await aioredis.create_redis('redis://127.0.0.1:6666/0')
        result = await conn.getset("add", json.dumps(dict(x=3, y=2)))
        result = json.loads(result)
        assert result == dict(result=5)
        conn.close()


async def common_command_check(conn: aioredis.Redis):
    info = await conn.info()
    assert "server" in info
    assert info["server"]["porkpepper_mode"] == "service"
    assert info["server"]["tcp_port"] == "6666"
    assert "keyspace" in info
    assert info["keyspace"]["db0"]["keys"] == "1"