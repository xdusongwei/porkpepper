from porkpepper.redis_protocol import RedisProtocol


def test_get_integer():
    assert RedisProtocol.get_integer(b"").is_error
    assert RedisProtocol.get_integer(b":\r\n").is_error
    assert RedisProtocol.get_integer(b":\n").is_error
    assert RedisProtocol.get_integer(b":1\n").is_error
    assert RedisProtocol.get_integer(b":-1\r\n").unwrap() == -1
    assert RedisProtocol.get_integer(b":0\r\n").unwrap() == 0
    assert RedisProtocol.get_integer(b":100000\r\n").unwrap() == 100000
    assert RedisProtocol.get_integer(None).is_error
    assert RedisProtocol.get_integer(1).is_error


def test_get_count():
    assert RedisProtocol.get_count(b"").is_error
    assert RedisProtocol.get_count(b"*\r\n").is_error
    assert RedisProtocol.get_count(b"*\n").is_error
    assert RedisProtocol.get_count(b"*1\n").is_error
    assert RedisProtocol.get_count(b"*-1\r\n").is_error
    assert RedisProtocol.get_count(b"*0\r\n").unwrap() == 0
    assert RedisProtocol.get_count(b"*100000\r\n").unwrap() == 100000
    assert RedisProtocol.get_count(None).is_error
    assert RedisProtocol.get_count(1).is_error


def test_get_size():
    assert RedisProtocol.get_binary_size(b"").is_error
    assert RedisProtocol.get_binary_size(b"$\r\n").is_error
    assert RedisProtocol.get_binary_size(b"$\n").is_error
    assert RedisProtocol.get_binary_size(b"$1\n").is_error
    assert RedisProtocol.get_binary_size(b"$-1\r\n").is_error
    assert RedisProtocol.get_binary_size(b"$0\r\n").unwrap() == 0
    assert RedisProtocol.get_binary_size(b"$100000\r\n").unwrap() == 100000
    assert RedisProtocol.get_binary_size(None).is_error
    assert RedisProtocol.get_binary_size(1).is_error


def test_set_nil():
    assert RedisProtocol.set_nil().unwrap() == b"$-1\r\n"


def test_set_integer():
    assert RedisProtocol.set_integer("").is_error
    assert RedisProtocol.set_integer(-1).unwrap() == b":-1\r\n"
    assert RedisProtocol.set_integer(False).is_error
    assert RedisProtocol.set_integer(None).is_error


def test_set_ok():
    assert RedisProtocol.set_ok().unwrap() == b"+OK\r\n"
    assert RedisProtocol.set_ok(0).is_error
    assert RedisProtocol.set_ok(None).is_error
    assert RedisProtocol.set_ok("TEST_-test").unwrap() == b"+TEST_-test\r\n"


def test_set_err():
    assert RedisProtocol.set_err().unwrap() == b"-ERR\r\n"
    assert RedisProtocol.set_err(0).is_error
    assert RedisProtocol.set_err(None).is_error
    assert RedisProtocol.set_err("TEST_-test").unwrap() == b"-TEST_-test\r\n"


def test_set_count():
    assert RedisProtocol.set_count(0).unwrap() == b"*0\r\n"
    assert RedisProtocol.set_count(100).unwrap() == b"*100\r\n"
    assert RedisProtocol.set_count(False).is_error
    assert RedisProtocol.set_count(-1).is_error
    assert RedisProtocol.set_count(None).is_error
    assert RedisProtocol.set_count("TEST_-test").is_error


def test_set_binary():
    assert RedisProtocol.set_binary("1234").unwrap() == b"$4\r\n1234\r\n"
    assert RedisProtocol.set_binary(b"1234").unwrap() == b"$4\r\n1234\r\n"
    assert RedisProtocol.set_binary(1234).unwrap() == b"$4\r\n1234\r\n"
    assert RedisProtocol.set_binary(None).is_error
    assert RedisProtocol.set_binary(False).is_error
    assert RedisProtocol.set_binary(1.2).is_error

