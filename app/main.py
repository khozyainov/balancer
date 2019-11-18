import os
from urllib.parse import urlsplit, urljoin

from sanic import Sanic
from sanic.response import redirect, HTTPResponse

from app.utils import Cache, Scheduler

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
ADDRESS = f"redis://{REDIS_HOST}:{REDIS_PORT}"

app = Sanic()
cache = Cache(ADDRESS).cache
sc = Scheduler(cache)


@app.route('/')
async def index(request):
    file_url = request.args.get('video')

    if file_url:
        splitted = urlsplit(file_url)
        srv_in_cluster, origin_host = splitted.netloc.split('.')
        path = splitted.path
    else:
        return HTTPResponse(status=400)

    server = await sc.get_server()

    if server:
        if server != origin_host:
            url = urljoin(f'http://{server}/{srv_in_cluster}/', path.lstrip('/'))
            return redirect(url)
        else:
            return redirect(file_url)
    else:
        return HTTPResponse(status=503)


@app.route('/configurate')
async def configurate(request):
    # TODO init or update cache with new weights
    # TODO add logging
    # TODO add tests
    pass


if __name__ == "__main__":
    app.create_server(HOST, PORT)
