import asyncio
import logging
import os

import aioredis
import uvloop

asyncio.set_event_loop(uvloop.new_event_loop())

SERVICE = os.getenv('SERVICE', 'balancer')


class Cache:
    def __init__(self, address):
        self.logger = logging.getLogger(SERVICE)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._init(address))
        self.logger.debug('connected to cache')

    async def _init(self, address):
        self._cache = await aioredis.create_redis_pool(
            address=address,
            minsize=2,
            maxsize=1000,
            encoding="utf-8",
        )

    @property
    def cache(self):
        return self._cache

    @staticmethod
    def setup_cache(address):
        return Cache(address).cache
