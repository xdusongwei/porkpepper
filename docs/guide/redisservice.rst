Redis服务
=========


Redis命令约定
------------


下面一些 Redis 命令默认设置了一些行为

* `SELECT`: 切换会话的当前数据库
* `GET`: 获取键所属接口的信息
* `SET`: 使用value参数来执行键所属接口，不要求返回结果
* `GETSET`: 使用value参数来执行键所属接口，要求返回结果
* `INFO`: 报告当前节点的信息，例如节点类型，基本状态等等
* `KEYS`/`SCAN`: 遍历当前数据库下可用接口的键列表

注意， ``AUTH`` 命令默认是无密码的，如果需要设置节点密码策略，
需要 继承 :class:`ServiceBasedRedisServer` 并编写 
:attr:`auth(self, session, password: bytes)` 方法的实现逻辑，
再使用定制的类去设置节点 :class:`RedisServiceNode` 的 :attr:`redis_server` 参数。


使用@service装饰器注册服务
-----------------------


:class:`RedisServiceNode` 需要提供包含接口服务的 ``类`` 或者 ``对象`` , 
需要在提供服务的 ``类`` 或者 ``对象`` 中, 通过使用 @service 装饰器注册一些接口信息::

    def service(key: str, output: bool = False, description: Optional[str] = None, meta: Optional[Dict] = None):

``key`` 参数将会绑定到 Redis 服务的键. 
``output`` 参数定义了服务函数是否需要返回结果.
``description`` 参数可以设置关于此服务的一些说明信息.
``meta`` 参数是一个字典结果, 允许使用者定制一些自己的接口信息.


多服务绑定数据库
--------------



热替换服务
---------

