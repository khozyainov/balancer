import asyncio, json
from math import gcd as math_gcd
from functools import reduce

import aioredis

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


class Scheduler:
    def __init__(self, cache):
        self.cache = cache

    async def _init(self, servers):
        self.orig_servers = dict(servers)
        self.servers = [(k, v) for k, v in self.orig_servers.items()]
        self.max = max(self.servers, key=lambda x: x[1])[1]
        self.gcd = reduce(math_gcd, [weight for _, weight in self.servers])
        self.length = len(self.servers)
        self.i = -1
        self.cw = 0

    async def check_configuration(self):
        _origin_cfg = await self.cache.get('cfg')
        origin_cfg = json.loads(_origin_cfg)
        if self.orig_servers != origin_cfg:
            await self.set_servers(origin_cfg)

    async def schedule(self):
        await self.check_configuration()
        while True:
            self.i = await self.cache.get('i', self.i)
            self.i = await self.cache.get('i', self.i)
            self.i = (self.i + 1) % self.length
            if self.i == 0:
                self.cw = self.cw - self.gcd
                if self.cw <= 0:
                    self.cw = self.max
                    if self.cw == 0:
                        return None
            if self.servers[self.i][1] >= self.cw:
                await self.cache.set('i', self.i)
                return self.servers[self.i]

    async def set_servers(self, servers):
        await self._init(servers)


class Cache:
    def __init__(self, address):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._init(address))

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
