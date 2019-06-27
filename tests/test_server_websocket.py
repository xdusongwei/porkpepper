import json
import asyncio
import pytest
import aiohttp
import aioredis
from porkpepper import *
from porkpepper.design import *


SESSION_ID = None


class Session(WebsocketSession):
    async def prepare(self):
        global SESSION_ID
        SESSION_ID = self.session_id

    async def request(self, message):
        assert len(self.session_id) == 24
        if message["type"] == "login":
            user = message.get("user")
            self.current_user = user
            await self.send(dict(type="login", user=user))
        elif message["type"] == "logout":
            self.current_user = None
            await self.send(dict(type="logout"))
        else:
            await self.close()


@pytest.mark.asyncio
async def test_websocket():
    node = WebsocketNode(Session, "/stream")
    await node.start(host="127.0.0.1", port=9090)
    conn_session = await aioredis.create_redis('redis://127.0.0.1:6379/0')
    conn_user = await aioredis.create_redis('redis://127.0.0.1:6379/1')
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect('http://127.0.0.1:9090/stream') as ws:
            # session exists
            session = await conn_session.get(SESSION_ID)
            session = json.loads(session)
            assert session
            # session = 1, user = 0
            session_count = await conn_session.dbsize()
            assert session_count == 1
            user_count = await conn_user.dbsize()
            assert user_count == 0
            session_keys = await conn_session.keys("*")
            assert len(session_keys) == 1
            user_keys = await conn_user.keys("*")
            assert len(user_keys) == 0
            # session = 1, user = 1
            await ws.send_json(dict(type="login", user="kenny"))
            message = await ws.receive_json(timeout=1)
            assert message == {"type": "login", "user": "kenny"}
            session_count = await conn_session.dbsize()
            assert session_count == 1
            user_count = await conn_user.dbsize()
            assert user_count == 1
            session_keys = await conn_session.keys("*")
            assert len(session_keys) == 1
            user_keys = await conn_user.keys("*")
            assert len(user_keys) == 1
            # fetch user kenny
            user = await conn_user.get("kenny")
            user = json.loads(user)
            assert user and len(user["sessions"]) == 1
            # logout user
            await ws.send_json(dict(type="logout"))
            message = await ws.receive_json(timeout=1)
            session_count = await conn_session.dbsize()
            assert session_count == 1
            user_count = await conn_user.dbsize()
            assert user_count == 0
            session_keys = await conn_session.keys("*")
            assert len(session_keys) == 1
            user_keys = await conn_user.keys("*")
            assert len(user_keys) == 0
            # login again
            await ws.send_json(dict(type="login", user="kenny"))
            message = await ws.receive_json(timeout=1)
            session_keys = await conn_session.keys("*")
            assert len(session_keys) == 1
            user_keys = await conn_user.keys("*")
            assert len(user_keys) == 1
            # offline
            await ws.close()

    # session = 0, user = 0
    session_count = await conn_session.dbsize()
    assert session_count == 0
    user_count = await conn_user.dbsize()
    assert user_count == 0
    databases = await conn_session.config_get("databases")
    assert databases["databases"] == "2"
    db_size = await conn_session.dbsize()
    assert db_size == 0
    # clean up
    conn_session.close()
    conn_user.close()
    await asyncio.gather(conn_session.wait_closed(), conn_user.wait_closed())
    await node.stop()
