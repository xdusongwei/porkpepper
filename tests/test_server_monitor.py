import asyncio
import pytest
import aioredis
import porkpepper


@pytest.mark.asyncio
async def test_monitor():
    node = porkpepper.SimpleMonitorNode()
    await node.start(host="127.0.0.1", port=9090, redis_host="127.0.0.1", redis_port=6379)
    with pytest.raises(aioredis.errors.ReplyError):
        await aioredis.create_redis('redis://127.0.0.1:6379/0')
    await asyncio.sleep(0.0)
    await node.stop()
