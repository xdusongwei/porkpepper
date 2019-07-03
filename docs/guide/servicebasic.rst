基础服务
=======


Redis命令控制
------------

目前 :mod:`porkpepper` 可以支持的 Redis 命令如下:

*   `SELECT`
*   `GET`
*   `SET`
*   `GETSET`
*   `AUTH`
*   `DEL`
*   `KEYS`
*   `SCAN`
*   `INFO`

如下 Redis 命令同样支持, 但其目的是让一些 Redis 客户端软件在连接 :mod:`porkpepper` 
服务时可以正常工作

*   `PING`
*   `DBSIZE`
*   `TTL`
*   `TYPE`
*   `CONFIG`

更多可支持命令的定义可以参见 :class:`RedisServer` 类, 通常 :mod:`porkpepper` 包装好的
节点会使用默认定制的 :class:`RedisServer` 派生类完成 Redis 命令, 
使用者可以重新设置自己的命令逻辑, 来设置节点对 Redis 命令的执行动作.

基本节点
-------

:class:`PorkPepperNode` 实例化需要提供如下参数

*   `redis_server`: 必须, 用于执行 Redis 命令的 :class:`RedisServer` 派生类
*   `session_class`: 可选, 如果需要运行 websocket 服务, 这里需要提供 :class:`WebsocketSession` 或派生类
*   `websocket_path`: 可选, 如果需要运行 websocket 服务, 此参数设置长连接 url
*   `**kwargs`: 可选, 其他参数将设置 :mod:`aiohttp` 的 :class:`Application` 参数


启动节点
-------

启动节点可以使用如下两种方式

*   使用 :func:`start` 异步启动任务, 并使用 :func:`stop` 异步关闭任务
*   使用 :func:`serve` 在当前任务启动

