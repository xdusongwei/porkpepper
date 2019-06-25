import time
import asyncio
import pytest
import porkpepper


async def sleep(gate, time):
    async with gate:
        await asyncio.sleep(time)


@pytest.mark.asyncio
async def test_gate():
    g = porkpepper.Gate(n=1)
    await g.open()
    async with g:
        pass
    start_time = time.time()
    await asyncio.gather(sleep(g, 0.2), sleep(g, 0.1), sleep(g, 0.1))
    end_time = time.time()
    assert 0.4 <= end_time - start_time < 0.5
    await g.close()
    await g.close_until_complete()

    status = porkpepper.ServerStatus()
    assert status.state == porkpepper.ServerStatusEnum.Zero
    await status.ready()
    assert status.state == porkpepper.ServerStatusEnum.Running
    await status.error()
    assert status.state == porkpepper.ServerStatusEnum.NotAvailable
    await status.left()
    assert status.state == porkpepper.ServerStatusEnum.Zero
