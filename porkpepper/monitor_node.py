import json
import asyncio
import aiotools
import aioredis
from .websocket_session import WebsocketSession
from .design import WebsocketNode


class Session(WebsocketSession):
    async def on_finish(self):
        print(self.session_id, "offline")


class SimpleMonitorNode(WebsocketNode):
    TIMER_TASK = None
    TIMER_INTERVAL = 2
    NODE_URL_LIST = list()

    def __init__(self, websocket_path="/monitor"):
        super(SimpleMonitorNode, self).__init__(session_class=WebsocketSession, websocket_path=websocket_path)

    async def publish_nodes_status(self, interval=0):
        report_list = list()
        for node_url in self.NODE_URL_LIST:
            connectivity = False
            conn = None
            info = None
            try:
                conn = await aioredis.create_redis(node_url)
                info = await conn.info()
                connectivity = True
            except OSError as e:
                connectivity = False
            finally:
                if conn:
                    conn.close()
                report_list.append(
                    {
                        "nodeUrl": node_url,
                        "connectivity": connectivity,
                        "info": info,
                    }
                )
        message = dict(type="report", detail=report_list)
        app = self._http_app
        if app is not None:
            all_sessions = self._http_app.all_sessions()
            send_list = [session.send(message) for session in all_sessions]
            if send_list:
                task = asyncio.Task(asyncio.gather(*send_list))
                asyncio.ensure_future(task)

    async def on_start(self):
        if self.TIMER_TASK:
            self.TIMER_TASK.cancel()
            self.TIMER_TASK = None
        self.TIMER_TASK = aiotools.create_timer(self.publish_nodes_status, self.TIMER_INTERVAL)

    async def on_shutdown(self):
        if self.TIMER_TASK:
            self.TIMER_TASK.cancel()
            self.TIMER_TASK = None


__all__ = ["SimpleMonitorNode", ]
