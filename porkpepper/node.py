from typing import *
import asyncio
from aiohttp import web
from .websocket_app import WebsocketApp
from .redis_server_default import DefaultRedisServer


class PorkPepperNode:
    def __init__(self, session_class=None, redis_server=None, websocket_path="/porkpepper", **kwargs):
        self._session_class = session_class

        self._app_options = kwargs or dict()
        self._http_app: WebsocketApp = WebsocketApp(session_class=session_class, **self._app_options)
        self._http_app.add_routes([web.route('GET', path, self._http_app.handler) for path in [websocket_path, ]])

        self._redis_server_class = redis_server if redis_server else DefaultRedisServer
        self._redis_server = self._redis_server_class(app=self._http_app)

        self._redis_server_task = None
        self._runner = None

    async def on_start(self):
        pass

    async def on_shutdown(self):
        pass

    async def __aenter__(self):
        return None

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()

    async def start(self, enable_websocket=False, redis_host="127.0.0.1", redis_port=6379, **kwargs):
        app = self._http_app
        redis_server = self._redis_server
        runner = web.AppRunner(app)
        self._runner = runner
        await runner.setup()
        if enable_websocket:
            site = web.TCPSite(runner, **kwargs)
            await site.start()
        await self.on_start()
        redis_server_task = asyncio.Task(redis_server.serve(redis_host, redis_port))
        asyncio.ensure_future(redis_server_task)
        self._redis_server_task = redis_server_task
        await asyncio.sleep(0.1)
        return self

    async def stop(self):
        await self.on_shutdown()
        if self._redis_server_task:
            self._redis_server_task.cancel()
            self._redis_server_task = None
        if self._runner:
            await self._runner.cleanup()
            self._runner = None

    async def serve(self, enable_websocket=False, redis_host="127.0.0.1", redis_port=6379, **kwargs):
        app = self._http_app
        redis_server = self._redis_server
        runner = web.AppRunner(app)
        await runner.setup()
        try:
            if enable_websocket:
                site = web.TCPSite(runner, **kwargs)
                await site.start()
            await self.on_start()
            await redis_server.serve(redis_host, redis_port)
        finally:
            await runner.cleanup()
            await self.on_shutdown()
