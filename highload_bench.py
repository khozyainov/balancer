import asyncio
import time

from aiohttp import ClientSession

NUMBER = 1000
SEMAPHORE = 500

BASE_URL = 'http://0.0.0.0:8000'
CONFIG_URL = f'{BASE_URL}/configurate'
CONFIG = {
    "https://ya.ru": 10, 
    "https://apple.com": 20, 
    "https://vk.com": 1
}

PARAMS = {'video': '/'}
URL = BASE_URL


count = {}

async def configurate():
    async with ClientSession() as session:
        async with session.post(CONFIG_URL, json=CONFIG) as resp:
            if resp.status != 200:
                raise Exception(
                    'Error on configurate, check balancer is running')
            print('configurate success')
            await asyncio.sleep(1)


async def fetch(url, session):
    async with session.get(url, params=PARAMS, ssl=False, allow_redirects=False) as response:
        redirect_to = response.headers.get('Location','')
        count[redirect_to] = count.get(redirect_to, 0) + 1


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


loop = asyncio.get_event_loop()
loop.run_until_complete(configurate())

future = asyncio.ensure_future(run(NUMBER))
start = time.time()
loop.run_until_complete(future)
finished = time.time()
print('Total sec: ', finished - start)
print(count)