快速指引: 创建Redis节点
=====================


编写服务
-------

最简单的创建方式是编写服务类，对于其中允许作为Redis接口的方法，
使用@service装饰器来设定其使用的Redis键，是否会返回数据，
其他自定义的接口数据描述等等参数::

   class MyService:
        @classmethod
        @service(key="add", output=True)
        async def add(cls, message):
            a = int(message.get("a", 0))
            b = int(message.get("b", 0))
            result = a + b
            return dict(result=result)

        @classmethod
        @service(key="action")
        async def action(cls, event_id, **kwargs):
            print("event_id is", event_id)


定义好服务类之后，需要设置Redis节点的数据库映射字典，来把服务类对应到指定的数据库上::

    db_map = {
        0: MyService,
    }


将映射字典设置到节点对象的参数中，并启动节点::

    node = RedisServiceNode()
    await node.start(db_map, redis_host="127.0.0.1", redis_port=6379)


使用 Redis 客户端访问 Redis 服务，可以查看服务接口信息，比如使用 ``GET action`` 命令::

    {
        "type": "api",
        "key":  "action",
        "output":  false,
        "signature":  "(cls, event_id, **kwargs)",
        "description":  null,
        "meta":  {
            
        }
    }


访问服务
-------


使用``aioredis``的``GETSET``命令操作``add``方法::

    conn = await aioredis.create_redis('redis://127.0.0.1:6379/0')
    result = await conn.getset("add", json.dumps(dict(a=1, b=2)))
    result = json.loads(result)
    assert result == dict(result=3)


使用``aioredis``的``SET``命令操作``action``方法::

    conn = await aioredis.create_redis('redis://127.0.0.1:6379/0')
    await conn.set("action", json.dumps(dict(event_id="myID")))