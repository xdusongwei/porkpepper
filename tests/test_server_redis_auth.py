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
    with pytest.raises(aioredis.errors.ReplyError):
        await aioredis.create_redis('redis://:123456@127.0.0.1:6379/0')

    # wrong password
    with pytest.raises(aioredis.errors.AuthError):
        await aioredis.create_redis('redis://:123@127.0.0.1:6379/0')

    # wrong password
    with pytest.raises(aioredis.errors.ReplyError):
        await aioredis.create_redis('redis://127.0.0.1:6379/0')

    await node.stop()
    await asyncio.sleep(0.1)
