import asyncio
import pytest
import aioredis
import porkpepper


class AuthRedisServer(porkpepper.ServiceBasedRedisServer):
    async def auth(self, session, password: bytes):
        return porkpepper.Result(password == b"123456")


@pytest.mark.asyncio
async def test_auth():
    node = porkpepper.RedisServiceNode(redis_server=AuthRedisServer)
    await node.start(redis_host="127.0.0.1", redis_port=6379)
    # right password
    try:
        conn = await aioredis.create_redis('redis://:123456@127.0.0.1:6379/0')
        conn.close()
        await asyncio.wait_for(conn.wait_closed(), 0.1)
        raise AssertionError
    except aioredis.ReplyError as e:
        assert e.args[0] == "ERR invalid DB index"
    except Exception as e:
        raise e
    finally:
        await asyncio.sleep(0.1)
    # wrong password
    try:
        conn = await aioredis.create_redis('redis://:123@127.0.0.1:6379/0')
        conn.close()
        await asyncio.wait_for(conn.wait_closed(), 0.1)
        raise AssertionError
    except aioredis.ReplyError as e:
        assert e.args[0] == "ERR invalid password"
    except Exception as e:
        raise e
    finally:
        await asyncio.sleep(0.1)
    await node.stop()
