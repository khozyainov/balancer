import json
import logging
import os
from functools import reduce
from math import gcd as math_gcd

from aioredis import MultiExecError

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
MODULUS_RANGE = 10000


class Scheduler:
    def __init__(self, cache):
        self.cache = cache
        self.logger = logging.getLogger(SERVICE)
        self.total_parts = 0
        self.modulus = {}

    async def get_server(self):
        cfg = await self.cache.get('cfg')
        self.logger.debug('get cfg: %s', cfg)
        if cfg:
            cfg = json.loads(cfg)
            length = len(cfg)
            if length != self.total_parts:
                self.modulus = json.loads(await self.cache.get('modulus'))
                self.total_parts = length
            i = await self.cache.incr('i')
            if i >= MODULUS_RANGE:
                await self.cache.set('i', 0)
                self.logger.debug('i > %s, reset to 0, old i: %s', MODULUS_RANGE, i)
                return cfg[i % self.total_parts]
            return cfg[self.modulus.get(i, 0)]
        else:
            return

    async def update_servers(self, servers):
        self._configurate(servers)
        scheduled_string = json.dumps(
            [self._schedule()[0] for _ in range(self.total_parts)])
        self.logger.debug('new schedule: %s', scheduled_string)
        self.modulus = {i: i % self.total_parts for i in range(MODULUS_RANGE)}
        await self._update_cache(scheduled_string, json.dumps(self.modulus))

    async def _update_cache(self, scheduled_string, modulus_string):
        await self.cache.watch('cfg', 'i', 'modulus')
        tr = self.cache.multi_exec()
        self.cache.set('i', 0)
        self.cache.set('cfg', scheduled_string)
        self.cache.set('modulus', modulus_string)
        try:
            await tr.execute()
        except MultiExecError:
            await self._update_cache(scheduled_string, modulus_string)

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

    @staticmethod
    def setup_scheduler(cache):
        return Scheduler(cache)
