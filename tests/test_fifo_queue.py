import asyncio
import pytest
from porkpepper import *


LOCK_ONE = asyncio.Event()
LOCK_TWO = asyncio.Event()
LOCK_THREE = asyncio.Event()


async def one(lock):
    async with lock:
        assert not LOCK_ONE.is_set() and not LOCK_TWO.is_set() and not LOCK_THREE.is_set()
        await asyncio.sleep(0.1)
        LOCK_ONE.set()


async def two(lock):
    async with lock:
        assert LOCK_ONE.is_set() and not LOCK_TWO.is_set() and not LOCK_THREE.is_set()
        await asyncio.sleep(0.2)
        LOCK_TWO.set()


async def three(lock):
    async with lock:
        assert LOCK_ONE.is_set() and LOCK_TWO.is_set() and not LOCK_THREE.is_set()
        await asyncio.sleep(0.3)
        LOCK_THREE.set()


@pytest.mark.asyncio
async def test_lock():
    lock = FifoLock()
    await asyncio.gather(one(lock), two(lock), three(lock))
    assert LOCK_ONE.is_set() and LOCK_TWO.is_set() and LOCK_THREE.is_set()
