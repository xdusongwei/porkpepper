import asyncio
import pytest
import aiohttp
from porkpepper import *


class HelloSession(WebsocketSession):
    async def request(self, message):
        assert len(self.session_id) == 24
        if message["type"] == "hello":
            await self.send(dict(type="world"))
        else:
            await self.close()


class PrepareAndFinishSession(WebsocketSession):
    CASE = ["on_finish", "prepare", ]

    async def prepare(self):
        assert self.CASE.pop() == "prepare"

    async def on_finish(self):
        assert self.CASE.pop() == "on_finish"


@pytest.mark.asyncio
async def test_basic_serve():
    node = PorkPepperNode(SocketBasedRedisServer, HelloSession)
    task = asyncio.Task(node.serve(enable_websocket=True, host="127.0.0.1", port=9090))
    await asyncio.sleep(0.01)
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/porkpepper') as ws:
            await ws.send_json(dict(type="hello"))
            message = await ws.receive_json(timeout=1)
            assert message == {"type": "world"}
            await ws.close()
    task.cancel()
    await asyncio.sleep(0.1)
    node = PorkPepperNode(SocketBasedRedisServer, PrepareAndFinishSession)
    task = asyncio.Task(node.serve(enable_websocket=True, host="127.0.0.1", port=9090))
    await asyncio.sleep(0.01)
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/porkpepper') as ws:
            await ws.close()
    assert not PrepareAndFinishSession.CASE
    task.cancel()


@pytest.mark.asyncio
async def test_basic_start():
    node = PorkPepperNode(SocketBasedRedisServer, HelloSession)
    await node.start(enable_websocket=True, host="127.0.0.1", port=9090)
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/porkpepper') as ws:
            await ws.send_json(dict(type="hello"))
            message = await ws.receive_json(timeout=1)
            assert message == {"type": "world"}
            await ws.close()
    await node.stop()
    node = PorkPepperNode(SocketBasedRedisServer, PrepareAndFinishSession)
    await node.start(enable_websocket=True, host="127.0.0.1", port=9090)
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/porkpepper') as ws:
            await ws.close()
    assert not PrepareAndFinishSession.CASE
    await node.stop()
