监控
====

所有类型的 :mod:`porkpepper` 服务都支持使用 Redis 命令 ``INFO`` 来汇报当前服务状态，
一般来讲，定时轮询 Redis 服务的 ``INFO`` 命令是监控服务的一种手段之一。


简单监控服务
----------

:mod:`porkpepper` 实现了一个简单版本的监控服务 :class:`SimpleMonitorNode`，
该服务基于 Websocket 向所有长连接会话周期性发送被监控节点数据。

:class:`SimpleMonitorNode` 节点有两个比较重要的类成员属性:

*   TIMER_INTERVAL: 被监控的 Redis 节点轮询 ``INFO`` 命令的周期, 单位是秒
*   NODE_URL_LIST: 被监控的 Redis 节点列表

