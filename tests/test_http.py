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
async def test_http():
    node = PorkPepperNode(HelloSession)
    server = asyncio.ensure_future(node.serve(enable_websocket=True, host="127.0.0.1", port=9090))
    await asyncio.sleep(0.01)
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/porkpepper') as ws:
            await ws.send_json(dict(type="hello"))
            message = await ws.receive_json(timeout=1)
            assert message == {"type": "world"}
            await ws.close()
    server.cancel()
    await asyncio.sleep(0.1)
    node = PorkPepperNode(PrepareAndFinishSession)
    server = asyncio.ensure_future(node.serve(enable_websocket=True, host="127.0.0.1", port=9090))
    await asyncio.sleep(0.01)
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/porkpepper') as ws:
            await ws.close()
    assert not PrepareAndFinishSession.CASE
    server.cancel()

