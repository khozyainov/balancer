import asyncio
import os
from urllib.parse import urljoin, urlsplit

import uvloop
from sanic import Sanic
from sanic.exceptions import InvalidUsage
from sanic.response import HTTPResponse, redirect

from logger import set_logger
from utils import Cache, Scheduler

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
ADDRESS = f"redis://{REDIS_HOST}:{REDIS_PORT}"
SERVICE_NAME = os.getenv('SERVICE', 'balancer')

asyncio.set_event_loop(uvloop.new_event_loop())

app = Sanic()
cache = Cache(ADDRESS).cache
sc = Scheduler(cache)

logger = set_logger(SERVICE_NAME)


@app.route('/')
async def index(request):
    file_url = request.args.get('video')
    logger.debug('file_url: %s', file_url)

    if file_url:
        splitted = urlsplit(file_url)
        srv_in_cluster, origin_host = splitted.netloc.split('.')
        path = splitted.path
    else:
        logger.error('no file_url')
        return HTTPResponse(status=400)

    try:
        server = await sc.get_server()
    except Exception as e:
        logger.debug('unexpected error on choosing server: %s', e)
        return HTTPResponse(status=500)

    logger.debug('choosen server: %s', server)

    if server:
        if server != origin_host:
            url = urljoin(f'http://{server}/{srv_in_cluster}/',
                          path.lstrip('/'))
            logger.debug('redirect to: %s', url)
            return redirect(url)
        else:
            logger.debug('redirect to: %s', file_url)
            return redirect(file_url)
    else:
        logger.error('no server available')
        return HTTPResponse(status=503)


@app.route('/configurate', methods=['POST'])
async def configurate(request):
    try:
        configuration = request.json
        logger.debug('configuration: %s', configuration)
    except InvalidUsage:
        return HTTPResponse(status=400)

    if configuration:
        try:
            await sc.update_servers(configuration)
            logger.debug('configuration succedded')
            return HTTPResponse()
        except Exception as e:
            logger.error('failed to configurate: %s', e)
            return HTTPResponse(status=500)


if __name__ == "__main__":
    server = app.create_server(HOST,
                               PORT,
                               debug=True,
                               access_log=False,
                               return_asyncio_server=True)
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(server)
    loop.run_forever()
