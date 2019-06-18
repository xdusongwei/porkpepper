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
