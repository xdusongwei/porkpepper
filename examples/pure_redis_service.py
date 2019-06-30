import json
import asyncio
import aioredis
from porkpepper.design import service, RedisServiceNode


class MyService:
    @classmethod
    @service(key="add", output=True)
    async def add(cls, message):
        a = int(message.get("a", 0))
        b = int(message.get("b", 0))
        result = a + b
        return dict(result=result)

    @classmethod
    @service(key="action")
    async def action(cls, event_id, **kwargs):
        print("event_id is", event_id)


async def main():
    node = RedisServiceNode()
    db_map = {
        0: MyService,
    }
    await node.start(db_map, redis_host="127.0.0.1", redis_port=6379)
    conn = await aioredis.create_redis('redis://127.0.0.1:6379/0')
    result = await conn.getset("add", json.dumps(dict(a=10, b=3)))
    result = json.loads(result)
    assert result["result"] == 13
    await conn.set("action", json.dumps(dict(event_id=13)))
    conn.close()
    await conn.wait_closed()
    await node.stop()


if __name__ == '__main__':
    asyncio.run(main())
