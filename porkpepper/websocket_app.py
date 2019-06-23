from typing import *
from collections import defaultdict
import aiohttp
from aiohttp import web
from .websocket_session import WebsocketSession


class WebsocketApp(web.Application):
    def __init__(self, session_class=WebsocketSession, **kwargs):
        super(WebsocketApp, self).__init__(**kwargs)
        self._session_class = session_class
        self._session_dict: Dict[str, WebsocketSession] = dict()
        self._user_dict: Dict[str, Set[WebsocketSession]] = defaultdict(set)

    def all_sessions(self):
        return list(self._session_dict.values())

    def all_users(self):
        return list(self._user_dict.keys())

    @property
    def sessions_count(self) -> int:
        return len(self._session_dict)

    @property
    def users_count(self) -> int:
        return len(self._user_dict)

    def get_session(self, session_id: str):
        return self._session_dict.get(session_id, None)

    def get_user(self, user: str) -> Set[WebsocketSession]:
        return self._user_dict.get(user, set())

    def __getitem__(self, item) -> WebsocketSession:
        return self._session_dict.__getitem__(item)

    def __contains__(self, item):
        return self._session_dict.__contains__(item)

    def remove_user(self, user, session):
        if user is not None and user in self._user_dict and session in self._user_dict[user]:
            self._user_dict[user].remove(session)
            if not len(self._user_dict[user]):
                self._user_dict.pop(user)

    def add_user(self, user, session):
        if user is not None:
            self._user_dict[user].add(session)

    def remove_session(self, session_id):
        if session_id in self._session_dict:
            self._session_dict.pop(session_id)

    def add_session(self, session_id, session):
        self._session_dict[session_id] = session

    async def handler(self, request):
        if not self._session_class:
            return
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        session = self._session_class()
        session.socket = ws
        session.app = self
        self.add_session(session.session_id, session)
        await session.prepare()
        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT or msg.type == aiohttp.WSMsgType.BINARY:
                    message_result = session.message_loads(msg.data)
                    if message_result.is_some:
                        await session.request(message_result.unwrap())
                elif msg.type == aiohttp.WSMsgType.ERROR or msg.type == aiohttp.WSMsgType.CLOSE:
                    break
        finally:
            try:
                await ws.close()
            except Exception as e:
                pass
            try:
                await session.on_finish()
            except Exception as e:
                pass
        if session.current_user:
            self.remove_user(session.current_user, session)
        self.remove_session(session.session_id)
        session.app = None
        session.socket = None
        return ws


__all__ = ["WebsocketApp", ]
