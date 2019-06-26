from porkpepper.redis_protocol import RedisProtocol


def test_integer():
    assert RedisProtocol.get_integer(b"").is_error
    assert RedisProtocol.get_integer(b":\r\n").is_error
    assert RedisProtocol.get_integer(b":\n").is_error
    assert RedisProtocol.get_integer(b":1\n").is_error
    assert RedisProtocol.get_integer(b":-1\r\n").unwrap() == -1
    assert RedisProtocol.get_integer(b":0\r\n").unwrap() == 0
    assert RedisProtocol.get_integer(b":100000\r\n").unwrap() == 100000


def test_count():
    assert RedisProtocol.get_count(b"").is_error
    assert RedisProtocol.get_count(b"*\r\n").is_error
    assert RedisProtocol.get_count(b"*\n").is_error
    assert RedisProtocol.get_count(b"*1\n").is_error
    assert RedisProtocol.get_count(b"*-1\r\n").is_error
    assert RedisProtocol.get_count(b"*0\r\n").unwrap() == 0
    assert RedisProtocol.get_count(b"*100000\r\n").unwrap() == 100000


def test_size():
    assert RedisProtocol.get_binary_size(b"").is_error
    assert RedisProtocol.get_binary_size(b"$\r\n").is_error
    assert RedisProtocol.get_binary_size(b"$\n").is_error
    assert RedisProtocol.get_binary_size(b"$1\n").is_error
    assert RedisProtocol.get_binary_size(b"$-1\r\n").is_error
    assert RedisProtocol.get_binary_size(b"$0\r\n").unwrap() == 0
    assert RedisProtocol.get_binary_size(b"$100000\r\n").unwrap() == 100000
