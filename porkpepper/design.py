from typing import *
import json
import inspect
from .error import *
from .result import Result
from .node import PorkPepperNode
from .redis_server import RedisServer


PORKPEPPER_ATTR = "__porkpepper__"


class WebsocketNode(PorkPepperNode):
    pass


def service(key: str, output: bool = False, description: Optional[str] = None, meta: Optional[Dict] = None):
    def wrap(func):
        setattr(func, PORKPEPPER_ATTR, dict(
            key=key,
            output=output,
            description=description,
            meta=meta if meta else dict()
        ))
        return func

    return wrap


class ServiceBasedRedisServer(RedisServer):
    MAX_DB_COUNT = 0
    SERVICE_MAP = dict()

    async def get(self, session, key) -> Result[bytes]:
        if session.current_db < 0 or session.current_db >= self.MAX_DB_COUNT:
            return Result(DatabaseNotFound())
        current_service = self.SERVICE_MAP.get(session.current_db, None)
        if not current_service:
            return Result(DatabaseNotFound())
        service_map = current_service["map"]
        service_dict = service_map.get(key, None)
        if not service_dict:
            return Result(None)
        service_arguments = service_dict["args"]
        output = {
            "type": "api",
            "key": service_arguments["key"],
            "output": service_arguments["output"],
            "description": service_arguments["description"],
            "meta": service_arguments["meta"],
        }
        return Result(json.dumps(output))

    async def getset(self, session, key, value) -> Result:
        if session.current_db < 0 or session.current_db >= self.MAX_DB_COUNT:
            return Result(DatabaseNotFound())
        current_service = self.SERVICE_MAP.get(session.current_db, None)
        if not current_service:
            return Result(DatabaseNotFound())
        service_map = current_service["map"]
        service_dict = service_map.get(key, None)
        if not service_dict:
            return Result(KeyNotFound())
        handler = service_dict["handler"]
        service_arguments = service_dict["args"]
        loads = current_service["loads"]
        dumps = current_service["dumps"]
        if not service_arguments.get("output", False):
            return Result(WrongCommand())
        try:
            message = loads(value)
            result = await handler(message=message)
            return Result(dumps(result))
        except Exception as e:
            return Result(e)

    async def set(self, session, key, value) -> Result:
        if session.current_db < 0 or session.current_db >= self.MAX_DB_COUNT:
            return Result(DatabaseNotFound())
        current_service = self.SERVICE_MAP.get(session.current_db, None)
        if not current_service:
            return Result(DatabaseNotFound())
        service_map = current_service["map"]
        service_dict = service_map.get(key, None)
        if not service_dict:
            return Result(KeyNotFound())
        handler = service_dict["handler"]
        loads = current_service["loads"]
        try:
            message = loads(value)
            await handler(message=message)
            return Result(True)
        except Exception as e:
            return Result(e)

    async def key_type(self, session, key):
        return Result("string")

    async def ping(self, session):
        return Result("PONG")

    async def info(self, session):
        service_list = list()
        for db in range(self.MAX_DB_COUNT):
            service_list.append(
                (db,
                 dict(
                     keys=len(self.SERVICE_MAP.get(db, dict()).get("map", list())),
                 )
                 ))
        info = self.INFO_TEMPLATE.render(port=self.port, porkpepper_mode="service", service_list=service_list)
        return Result(info)

    async def ttl(self, session, key):
        return Result(-1)

    async def scan(self, session, pattern):
        if session.current_db < 0 or session.current_db >= self.MAX_DB_COUNT:
            return Result(DatabaseNotFound())
        current_service = self.SERVICE_MAP.get(session.current_db, None)
        if not current_service:
            return Result(list())
        service_map = current_service["map"]
        return Result(list(service_map.keys()))

    async def dbsize(self, session):
        if session.current_db < 0 or session.current_db >= self.MAX_DB_COUNT:
            return Result(DatabaseNotFound())
        current_service = self.SERVICE_MAP.get(session.current_db, None)
        if not current_service:
            return Result(0)
        service_map = current_service["map"]
        return Result(len(service_map))

    async def select(self, session, db):
        if 0 <= db < self.MAX_DB_COUNT:
            session.current_db = db
            return Result(True)
        else:
            return Result(DatabaseNotFound())

    async def config(self, session, get_set, field, value=None):
        if get_set == b'GET' and field == b'databases':
            return Result([b'databases', f'{self.MAX_DB_COUNT}'.encode("utf8")])
        return Result(CommandNotFound())


class RedisServiceNode(PorkPepperNode):
    def __init__(self, **kwargs):
        super(RedisServiceNode, self).__init__(**kwargs)
        self._services = dict()
        self._redis_server_class = ServiceBasedRedisServer
        self._redis_server = self._redis_server_class(app=self._http_app)

    async def update_service(self, db: int, new_service: Type):
        members = inspect.getmembers(new_service, inspect.ismethod)
        service_map = dict()
        for _, member in members:
            if not inspect.iscoroutinefunction(member):
                continue
            sign = inspect.signature(member)
            if "message" not in sign.parameters:
                continue
            if not hasattr(member, PORKPEPPER_ATTR):
                continue
            service_arguments = getattr(member, PORKPEPPER_ATTR)
            key = service_arguments.get("key", None)
            if key in service_map:
                raise KeyError
            if not isinstance(key, str):
                raise ValueError
            service_map[key] = dict(handler=member, args=service_arguments)
        loads = getattr(new_service, "LOADS", json.loads)
        dumps = getattr(new_service, "DUMPS", json.dumps)
        self._services[db] = dict(loads=loads, dumps=dumps, map=service_map)
        if self._redis_server:
            if db + 1 > self._redis_server.MAX_DB_COUNT:
                self._redis_server.MAX_DB_COUNT = db + 1
            self._redis_server.SERVICE_MAP = self._services
            
    async def _initialize_service_map(self, service_map: Dict[int, Type] = None):
        if service_map:
            for db, service_type in service_map.items():
                if not isinstance(db, int):
                    raise ValueError
                await self.update_service(db, service_type)

    async def start(self, service_map: Dict[int, Type] = None, redis_host="127.0.0.1", redis_port=6379, **kwargs):
        await self._initialize_service_map(service_map)
        return await super(RedisServiceNode, self).start(
            enable_websocket=False,
            redis_host=redis_host,
            redis_port=redis_port, **kwargs
        )

    async def serve(self, service_map: Dict[int, Type] = None, redis_host="127.0.0.1", redis_port=6379, **kwargs):
        await self._initialize_service_map(service_map)
        await super(RedisServiceNode, self).serve(
            enable_websocket=False,
            redis_host=redis_host,
            redis_port=redis_port,
            **kwargs
        )


__all__ = ["WebsocketNode", "RedisServiceNode", "service", ]
