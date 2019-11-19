import os
from urllib.parse import urljoin, urlsplit

from sanic.exceptions import InvalidUsage
from sanic.response import HTTPResponse, redirect

from app.cache import Cache
from app.logger import set_logger
from app.scheduler import Scheduler

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
ADDRESS = f"redis://{REDIS_HOST}:{REDIS_PORT}"
SERVICE_NAME = os.getenv('SERVICE', 'balancer')

cache = Cache.setup_cache(ADDRESS)
sc = Scheduler.setup_scheduler(cache)

logger = set_logger(SERVICE_NAME, file_logging=True)


async def index(request):
    file_url = request.args.get('video')
    logger.debug('file_url: %s', file_url)

    if file_url:
        splitted = urlsplit(file_url)
        origin_host = splitted.netloc
        path = splitted.path
    else:
        logger.error('no file_url')
        return HTTPResponse(status=400)

    try:
        server = await sc.get_server()
    except Exception as e:
        logger.error('unexpected error on choosing server: %s', e)
        return HTTPResponse(status=500)

    logger.debug('choosen server: %s', server)

    if server:
        if urlsplit(server).netloc != origin_host:
            url = urljoin(f'{server}', path.lstrip('/'))
            logger.debug('redirect to cdn: %s', url)
            return redirect(url)
        else:
            logger.debug('redirect to origin: %s', file_url)
            return redirect(file_url)
    else:
        logger.error('no server available')
        return HTTPResponse(status=503)


async def configurate(request):
    try:
        configuration = request.json
        logger.debug('configuration: %s', configuration)
    except InvalidUsage:
        logger.error('invalid configuration')
        return HTTPResponse(status=400)

    if configuration:
        try:
            await sc.update_servers(configuration)
            logger.debug('configuration succedded')
            return HTTPResponse()
        except Exception as e:
            logger.error('failed to configurate: %s', e)
            return HTTPResponse(status=500)
    else:
        logger.error('empty configuration')
        return HTTPResponse(status=400)
