import asyncio

from backend.cache import AsyncTTLCache


async def test_basic_set_get():
    c = AsyncTTLCache()
    await c.set("k", "v", ttl=10)
    assert await c.get("k") == "v"


async def test_decorator_caches_calls():
    c = AsyncTTLCache()
    counter = {"n": 0}

    @c.cached("k:{x}", ttl=10)
    async def fn(x: int) -> int:
        counter["n"] += 1
        return x * 2

    assert await fn(3) == 6
    assert await fn(3) == 6
    assert counter["n"] == 1


async def test_decorator_single_flight():
    c = AsyncTTLCache()
    counter = {"n": 0}
    started = asyncio.Event()
    proceed = asyncio.Event()

    @c.cached("k:{x}", ttl=10)
    async def slow(x: int) -> int:
        counter["n"] += 1
        started.set()
        await proceed.wait()
        return x * 2

    task1 = asyncio.create_task(slow(7))
    await started.wait()
    task2 = asyncio.create_task(slow(7))
    await asyncio.sleep(0)  # let task2 reach the lock
    proceed.set()
    r1, r2 = await asyncio.gather(task1, task2)
    assert r1 == r2 == 14
    assert counter["n"] == 1
