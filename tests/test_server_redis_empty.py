import pytest
import porkpepper


@pytest.mark.asyncio
async def test_empty_redis_server():
    server = porkpepper.RedisServer()
    result = await server.get(None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.getset(None, None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.set(None, None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.key_type(None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.ping(None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.info(None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.auth(None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.ttl(None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.scan(None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.dbsize(None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.select(None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
    result = await server.config(None, None, None)
    assert result.is_error and isinstance(result.error, NotImplementedError)
