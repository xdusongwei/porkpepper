import pytest
import porkpepper


def test_result_none():
    r = porkpepper.Result()
    assert r.is_none
    assert not r.is_some
    assert not r.is_error
    assert r.is_ok
    assert not r.error

    r = porkpepper.Result.none()
    assert r.is_none
    assert not r.is_some
    assert not r.is_error
    assert r.is_ok
    assert not r.error


def test_result_some():
    r = porkpepper.Result(0)
    assert not r.is_none
    assert r.is_some
    assert not r.is_error
    assert r.is_ok
    assert not r.error


def test_result_ok():
    r = porkpepper.Result(1)
    assert not r.is_none
    assert r.is_some
    assert not r.is_error
    assert r.is_ok
    assert not r.error


def test_result_exception():
    r = porkpepper.Result(ValueError())
    assert not r.is_none
    assert not r.is_some
    assert r.is_error
    assert not r.is_ok
    assert r.error

    r = porkpepper.Result(ValueError)
    assert not r.is_none
    assert not r.is_some
    assert r.is_error
    assert not r.is_ok
    assert r.error


def test_unwrap():
    r = porkpepper.Result(0)
    assert r.unwrap() == 0
    r = porkpepper.Result(ValueError())
    with pytest.raises(porkpepper.UnwrapError):
        assert r.unwrap()
    r = porkpepper.Result(True)
    assert r.unwrap() == True
