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


CALL_WITHOUT_OUTPUT = False


class ServiceAtOne:
    @classmethod
    @service("plus", output=True, meta=dict(info="test_info"))
    async def plus(cls, message):
        x = message.get("x", 0)
        y = message.get("y", 0)
        return dict(result=x + y)

    @service("times", output=True)
    async def times(self, a, b, **kwargs):
        return dict(result=a * b)

    @service("noOutput")
    async def without_output(self, x, y=1, **kwargs):
        global CALL_WITHOUT_OUTPUT
        assert x == 1
        assert y == 2
        CALL_WITHOUT_OUTPUT = True


@pytest.mark.asyncio
async def test_address_conflict_start_node():
    node = RedisServiceNode()
    await node.start(service_map={0: ServiceAtZero, 1: ServiceAtOne()}, redis_host="127.0.0.1", redis_port=6379)
    node_2 = RedisServiceNode()
    with pytest.raises(IOError):
        await node_2.start(service_map={0: ServiceAtZero, 1: ServiceAtOne()}, redis_host="127.0.0.1", redis_port=6379)
    await node.stop()


@pytest.mark.asyncio
async def test_address_conflict_serve_node():
    node = RedisServiceNode()
    task = asyncio.Task(node.serve(service_map={0: ServiceAtZero, 1: ServiceAtOne()}, redis_host="127.0.0.1", redis_port=6379))
    await asyncio.wait_for(node.start_event.wait(), 0.1)
    node_2 = RedisServiceNode()
    with pytest.raises(IOError):
        await node_2.serve(service_map={0: ServiceAtZero, 1: ServiceAtOne()}, redis_host="127.0.0.1", redis_port=6379)
    task.cancel()
    await asyncio.wait_for(node.stop_event.wait(), 0.1)


@pytest.mark.asyncio
async def test_service():
    node = RedisServiceNode()
    await node.start(service_map={0: ServiceAtZero, 1: ServiceAtOne()}, redis_host="127.0.0.1", redis_port=6379)

    # db 0
    conn = await aioredis.create_redis('redis://127.0.0.1:6379/0')
    conn_db_0 = conn
    config = await conn.config_get("databases")
    assert config["databases"] == "2"
    result = await conn.getset("add", json.dumps(dict(x=1, y=2)))
    result = json.loads(result)
    assert result == dict(result=3)
    no_exists_command = await conn.get("xyz")
    assert no_exists_command is None
    add_command = await conn.get("add")
    assert add_command
    key_type = await conn.type("add")
    assert key_type == b"string"
    ttl = await conn.ttl("add")
    assert ttl == -1
    add_command = json.loads(add_command)
    assert add_command["key"] == "add"
    assert isinstance(add_command["output"], bool) and add_command["output"]
    assert add_command["description"] == "add function"
    dbsize = await conn.dbsize()
    assert dbsize == 1
    await common_command_check(conn)
    conn.close()

    # db 1
    conn = await aioredis.create_redis('redis://127.0.0.1:6379/1')
    conn_db_1 = conn
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
    await conn.set("noOutput", json.dumps(dict(x=1, y=2)))
    global CALL_WITHOUT_OUTPUT
    assert CALL_WITHOUT_OUTPUT
    db_size = await conn.dbsize()
    assert db_size == 3
    keys = await conn.keys("*")
    assert len(keys) == 3
    await common_command_check(conn)
    conn.close()

    await asyncio.gather(conn_db_0.wait_closed(), conn_db_1.wait_closed())
    await node.stop()


async def common_command_check(conn: aioredis.Redis):
    await conn.ping()
    info = await conn.info()
    assert "server" in info
    assert info["server"]["porkpepper_mode"] == "service"
    assert info["server"]["tcp_port"] == "6379"
    assert "keyspace" in info
    assert info["keyspace"]["db0"]["keys"] == "1"
