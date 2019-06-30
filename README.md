porkpepper
==========

使用 Redis 协议编写服务，以及使用 Redis 协议控制 Websocket 会话


示例: 启动一个 Redis 服务

```python
import asyncio
from porkpepper.design import service, RedisServiceNode


class MyService:
    @classmethod
    @service(key="add", output=True, meta=dict(version="0.1.0"))
    async def add(cls, message):
        a = message.get("a", 0)
        b = message.get("b", 0)
        result = a + b
        return dict(result=result)


class MyService2:
    @service(key="plus", output=True)
    async def add(self, x, y, **kwargs):
        result = x + y
        return dict(result=result)
    
    @service(key="without_output")
    async def without_output(self, message):
        print(message)


async def main():
    node = RedisServiceNode()
    # 设置类型和实例都可以
    db_map = {
        0: MyService,
        1: MyService2(),
    }
    await node.serve(db_map, redis_host="127.0.0.1", redis_port=6379)


if __name__ == '__main__':
    asyncio.run(main())

```

```
$ redis-cli
127.0.0.1:6379> KEYS *
1) "add"
127.0.0.1:6379> GETSET add "{\"a\": 1, \"b\": 2}"
"{\"result\": 3}"
127.0.0.1:6379> SELECT 1
OK
127.0.0.1:6379[1]> KEYS *
1) "plus"
2) "without_output"
127.0.0.1:6379[1]> GET plus
"{\"type\": \"api\", \"key\": \"plus\", \"output\": true, \"signature\": \"(self, x, y, **kwargs)\", \"description\": null, \"meta\": {}}"
127.0.0.1:6379[1]> GET without_output
"{\"type\": \"api\", \"key\": \"without_output\", \"output\": false, \"signature\": \"(self, message)\", \"description\": null, \"meta\": {}}"
127.0.0.1:6379[1]> GETSET plus "{\"x\": 1, \"y\": 2}"
"{\"result\": 3}"
127.0.0.1:6379[1]> SET without_output "{\"foo\": \"bar\"}"
OK
```




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
    node = porkpepper.WebsocketNode(HelloSession, "/porkpepper")
    await node.serve(host="127.0.0.1", port=9090)


async def client():
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/porkpepper') as ws:
            await ws.send_json(dict(type="hello"))
            message = await ws.receive_json()
            assert message == {"type": "world"}
            await ws.close()

```
