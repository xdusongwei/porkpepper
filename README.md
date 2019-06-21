porkpepper
==========

一种混合 Websocket 服务和 Redis 服务的框架


示例: 启动 Redis 和 Websocket 服务

```Python
import aiohttp
import porkpepper


class HelloSession(porkpepper.WebsocketSession):
    async def request(self, message):
        if message["type"] == "hello":
            await self.send(dict(type="world"))
        else:
            await self.close()


async def serve():
    node = porkpepper.PorkPepperNode(HelloSession)
    await node.serve(enable_websocket=True, host="127.0.0.1", port=9090)


async def client():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/porkpepper') as ws:
            await ws.send_json(dict(type="hello"))
            message = await ws.receive_json()
            assert message == {"type": "world"}
            await ws.close()

```

示例: 纯 Redis 服务


```Python
import asyncio
from porkpepper.design import service, RedisServiceNode


class MyService:
    @classmethod
    @service(key="add", output=True, meta=dict(version="0.1.0"))
    async def my_add(cls, message):
        a = message.get("a", 0)
        b = message.get("b", 0)
        result = a + b
        return dict(result=result)


class MyPureRedisServer(RedisServiceNode):
    async def on_start(self):
        await self.update_service(3, MyService)


async def work():
    node = MyPureRedisServer()
    await node.serve()


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(work())

```

```
$ redis-cli -n 3
127.0.0.1:6379[3]> GETSET add "{\"a\": 1, \"b\": 2}"
"{\"result\": 3}"
127.0.0.1:6379[3]> GET add
"{\"key\": \"add\", \"output\": true, \"meta\": {\"version\": \"0.1.0\"}}"
```
