import asyncio
import time

from aiohttp import ClientSession

URL = 'http://0.0.0.0:8000'
PARAMS = {'video': '/'} 
SEMAPHORE = 500

count = {}

async def fetch(url, session):
    async with session.get(url, params=PARAMS, ssl=False) as response:
        count[response.url] = count.get(response.url, 0) + 1


async def bound_fetch(sem, url, session):
    async with sem:
        await fetch(url, session)


async def run(r):
    tasks = []
    sem = asyncio.Semaphore(SEMAPHORE)

    async with ClientSession() as session:
        for i in range(r):
            task = asyncio.ensure_future(bound_fetch(sem, URL, session))
            tasks.append(task)

        await asyncio.gather(*tasks)

number = 100
loop = asyncio.get_event_loop()

future = asyncio.ensure_future(run(number))
start = time.time()
loop.run_until_complete(future)
finished = time.time()
print('Total sec: %s', finished-start)
print(count)