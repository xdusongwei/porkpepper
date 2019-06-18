from typing import *
import asyncio
from aiohttp import web
from .websocket_app import WebsocketApp
from .redis_server_default import DefaultRedisServer


class PorkPepperNode:
    def __init__(self, session_class=None, redis_server=None, **kwargs):
        self._app_options = kwargs or dict()
        self._redis_options = dict()
        self._http_app: WebsocketApp = None
        self._redis_server_class = redis_server if redis_server else DefaultRedisServer
        self._session_class = session_class
        self.runner = None

    async def on_start(self):
        pass

    async def on_shutdown(self):
        pass

    async def serve(self, enable_websocket=False, redis_host="127.0.0.1", redis_port=6379, websocket_path="/porkpepper", **kwargs):
        session_class = self._session_class
        app = WebsocketApp(session_class=session_class, **self._app_options)
        app.add_routes([web.route('GET', path, app.handler) for path in [websocket_path, ]])
        self._http_app = app
        redis_server = self._redis_server_class(app=app)
        redis_loop = redis_server.serve(redis_host, redis_port)
        redis_task = asyncio.ensure_future(redis_loop)
        runner = web.AppRunner(app)
        await runner.setup()
        await self.on_start()
        try:
            if enable_websocket:
                site = web.TCPSite(runner, **kwargs)
                await site.start()
            while True:
                await asyncio.sleep(60)
        finally:
            redis_task.cancel()
            await runner.cleanup()
            await self.on_shutdown()
