Websocket服务
============


Redis命令约定
------------

下面一些 Redis 命令默认设置了一些行为

* `SELECT`: 切换会话的当前数据库, db0 保存了当前节点的会话, db1 保存了当前节点的用户
* `GET`: 获取键所属接口的信息, db0 上可以得到会话的详细信息, db1 可以得到登录用户的详细信息
* `SET`: 在 db0 数据库时, 将 value 数据发送到指定会话; 在 db1 数据库时, 将 value 数据发送到指定用户的全部会话 
* `DEL`: 在 db0 数据库时, 可以使用这种方式要求指定的会话结束
* `INFO`: 报告当前节点的信息，例如节点类型，基本状态等等
* `KEYS`/`SCAN`: 遍历当前数据库下在线的会话或者用户


Websocket会话
-------------


:mod:`porkpepper` 会为每个新建立的会话设置 `会话ID` 字符串, 目前 `会话ID` 由 `SS`
开头, 共计 24 个字符.

对于 Websocket 服务, 需要使用者使用 :class:`WebsocketSession` 类创建继承类,
在其中 :func:`request` 函数来处理从 Websocket 接收到的数据.


:class:`WebsocketSession` 提供了一些方法帮助控制 Websocket 通信:

*   :attr:`current_user`: 获取或者设置会话的用户, 注意这个属性的对象应符合字符串类型
*   :func:`read_timeout`: 会话读取数据最大等待时间
*   :func:`prepare`: 会话开始时需要执行的逻辑
*   :func:`on_finish`: 会话结束前需要执行的逻辑
*   :func:`send`: 向 Websocket 发送数据
*   :func:`close`: 主动关闭会话
*   :func:`message_loads`: 从 Websocket 读取的数据如何解析, 默认使用 json.loads
*   :func:`message_dumps`: 发送到 Websocket 的数据如何打包, 默认使用 json.dumps
