Result<object>对象
==================


:class:`Result` 对象借鉴了 ``Rust`` 语言的 :class:`Result` 和 :class:`Option` 两种结构，
使得可以同时可以记录执行状态或者执行结果，内部比较少使用异常捕获的场景进行容错。

:class:`Result` 包含了 :attr:`is_ok` , :attr:`is_error` 属性来判断状态，
也存在 :attr:`is_some` , :attr:`is_none` 属性帮助判断结果是否存在。
