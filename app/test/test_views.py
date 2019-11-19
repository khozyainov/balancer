import asyncio

from asynctest.mock import patch
from unittest.mock import MagicMock
import pytest
import sys

sys.modules['app.cache'] = MagicMock()
sys.modules['app.logger'] = MagicMock()
sys.modules['app.scheduler'] = MagicMock()

from app.main import app

ORIGIN = 'http://test.test'
CDN = 'http://cdn.test'
PATH = '/video/test.mp4'
QUERY = {'video': f'{ORIGIN}{PATH}'}


@pytest.yield_fixture
def sanic_app():
    yield app


@pytest.fixture
def test_cli(loop, sanic_app, sanic_client):
    return loop.run_until_complete(sanic_client(sanic_app))


@patch('app.views.sc.get_server')
async def test_index_redirect_to_cdn(mock_sc, test_cli):
    f = asyncio.Future()
    f.set_result(CDN)
    mock_sc.return_value = f
    resp = await test_cli.get('/', params=QUERY, allow_redirects=False)
    assert resp.status == 302
    assert resp.headers['Location'] == f'{CDN}{PATH}'


@patch('app.views.sc.get_server')
async def test_index_redirect_to_origin(mock_sc, test_cli):
    f = asyncio.Future()
    f.set_result(ORIGIN)
    mock_sc.return_value = f
    resp = await test_cli.get('/', params=QUERY, allow_redirects=False)
    assert resp.status == 302
    assert resp.headers['Location'] == f'{ORIGIN}{PATH}'


@patch('app.views.sc.get_server')
async def test_index_no_servers(mock_sc, test_cli):
    f = asyncio.Future()
    f.set_result(None)
    mock_sc.return_value = f
    resp = await test_cli.get('/', params=QUERY, allow_redirects=False)
    assert resp.status == 503


@patch('app.views.sc.get_server')
async def test_index_get_server_exc(mock_sc, test_cli):
    mock_sc.side_effect = Exception()
    resp = await test_cli.get('/', params=QUERY)
    assert resp.status == 500


async def test_index_no_video(test_cli):
    resp = await test_cli.get('/')
    assert resp.status == 400


@patch('app.views.sc.update_servers')
async def test_configurate(mock_sc, test_cli):
    f = asyncio.Future()
    f.set_result(None)
    mock_sc.return_value = f
    resp = await test_cli.post('/configurate', data='{"2": 1}')
    assert resp.status == 200


async def test_configurate_invalid_conf(test_cli):
    resp = await test_cli.post('/configurate', data='{"2": }')
    assert resp.status == 400


@patch('app.views.sc.update_servers')
async def test_configurate_failed_to_conf(mock_sc, test_cli):
    mock_sc.side_effect = Exception()
    resp = await test_cli.post('/configurate', data='{"2": 1}')
    assert resp.status == 500