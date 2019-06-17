porkpepper
==========

一种混合 Websocket 服务和 Redis 服务的框架


```Python
import asyncio
import porkpepper


class MyNode(porkpepper.PorkPepperNode):
    async def timer(self):
        while True:
            await asyncio.sleep(2)
            app = self._http_app
            if app is None:
                continue
            sessions = self._http_app.all_sessions()
            for session in sessions:
                try:
                    await session.send(dict(text="good"))
                except Exception as e:
                    pass

    async def on_start(self):
        print("node started!")
        asyncio.ensure_future(self.timer())


class MySession(porkpepper.WebsocketSession):
    async def prepare(self):
        print(self.session_id)

    async def request(self, message):
        print(message)


class MyRedis(porkpepper.RedisServer):
    async def set(self, key, value):
        app: porkpepper.WebsocketApp = self.app
        try:
            if app is not None and key in app:
                await app[key].send(dict(text=str(value)))
        except Exception as e:
            print(e)
        return porkpepper.Result(True)


if __name__ == '__main__':
    node = MyNode(MyRedis(), MySession)
    node.serve(port=9090)

```