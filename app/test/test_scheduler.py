import asyncio
import json
import pytest

from asynctest.mock import patch
from unittest.mock import MagicMock
import pytest
import sys

from app.scheduler import Scheduler


def future(return_value):
    f = asyncio.Future()
    f.set_result(return_value)
    return f


@pytest.fixture
def test_sch():
    cache = MagicMock()
    return Scheduler.setup_scheduler(cache)


async def test_get_server_none(test_sch):
    test_sch.cache.get.return_value = future(None)
    assert None == await test_sch.get_server()


async def test_get_server(test_sch):
    SCHEDULED = {
        0: 'a',
        1: 'a',
        2: 'b',
        3: 'a',
        4: 'b',
        5: 'c',
        6: 'a',
        7: 'b',
        8: 'c'
    }
    UUID = 'abcd'
    NEXT = 5
    test_sch.cache.get.return_value = future(UUID)
    test_sch.config_uuid = UUID
    test_sch.cache.incr.return_value = future(NEXT)
    test_sch.scheduled = SCHEDULED
    test_sch.total_parts = len(SCHEDULED)
    test_sch.modulus = {NEXT: NEXT % len(SCHEDULED)}
    assert SCHEDULED[NEXT] == await test_sch.get_server()


def test_configurate(test_sch):
    SERVERS = {'a': 10, 'b': 20, 'c': 3}
    test_sch._configurate(SERVERS)
    assert test_sch.servers == [("a", 10), ("b", 20), ("c", 3)]
    assert test_sch.max == 20
    assert test_sch.gcd == 1
    assert test_sch.length == 3
    assert test_sch.total_parts == 33
    assert test_sch.i == -1
    assert test_sch.cw == 0


def test_schedule(test_sch):
    SERVERS = {'a': 4, 'b': 3, 'c': 2}
    SCHEDULED = [('a', 4), ('a', 4), ('b', 3), ('a', 4), ('b', 3), ('c', 2),
                 ('a', 4), ('b', 3), ('c', 2)]
    test_sch._configurate(SERVERS)
    assert SCHEDULED == [test_sch._schedule() for _ in range(len(SCHEDULED))]