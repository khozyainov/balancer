import asyncio
import json
import logging
import os
from functools import reduce
from math import gcd as math_gcd

import aioredis

# http://kb.linuxvirtualserver.org/wiki/Weighted_Round-Robin_Scheduling
# Supposing that there is a server set S = {S0, S1, …, Sn-1};
# W(Si) indicates the weight of Si;
# i indicates the server selected last time, and i is initialized with -1;
# cw is the current weight in scheduling, and cw is initialized with zero;
# max(S) is the maximum weight of all the servers in S;
# gcd(S) is the greatest common divisor of all server weights in S;
#
# while (true) {
#     i = (i + 1) mod n;
#     if (i == 0) {
#         cw = cw - gcd(S);
#         if (cw <= 0) {
#             cw = max(S);
#             if (cw == 0)
#                 return NULL;
#         }
#     }
#     if (W(Si) >= cw)
#         return Si;
# }
SERVICE = os.getenv('SERVICE', 'balancer')

class Scheduler:
    def __init__(self, cache):
        self.cache = cache
        self.logger = logging.getLogger(SERVICE)

    async def get_server(self):
        cfg = await self.cache.get('cfg')
        self.logger.debug('get cfg: %s', cfg)
        if cfg:
            cfg = json.loads(cfg)
            i = await self.cache.incr('i')
            if i < len(cfg):
                return cfg[i]
            else:
                await self.cache.set('i', 0)
                self.logger.debug('i > len(cfg), reset to 0, old i: %s', i)
                return await self.get_server()
        else:
            return

    async def update_servers(self, servers):
        self._configurate(servers)
        scheduled = json.dumps(
            [self._schedule()[0] for _ in range(0, self.total_parts)])
        self.logger.debug('new schedule: %s', scheduled)
        await self._update_cache(scheduled)

    async def _update_cache(self, scheduled):
        await self.cache.watch('cfg', 'i')
        tr = self.cache.multi_exec()
        self.cache.set('cfg', scheduled)
        self.cache.set('i', 0)
        try:
            await tr.execute()
        except aioredis.MultiExecError:
            await self._update_cache(scheduled)

    def _configurate(self, servers):
        self.orig_servers = dict(servers)
        self.servers = [(k, v) for k, v in self.orig_servers.items()]
        self.max = max(self.servers, key=lambda x: x[1])[1]
        self.gcd = reduce(math_gcd, [weight for _, weight in self.servers])
        self.length = len(self.servers)
        self.total_parts = sum(self.orig_servers.values())
        self.i = -1
        self.cw = 0

    def _schedule(self):
        while True:
            self.i = (self.i + 1) % self.length
            if self.i == 0:
                self.cw = self.cw - self.gcd
                if self.cw <= 0:
                    self.cw = self.max
                    if self.cw == 0:
                        return None
            if self.servers[self.i][1] >= self.cw:
                return self.servers[self.i]


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
            maxsize=500,
            encoding="utf-8",
        )

    @property
    def cache(self):
        return self._cache
