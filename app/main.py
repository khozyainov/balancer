import os

from sanic import Sanic
from sanic.response import redirect
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
    server = await sc.schedule()
    args = request.args
    

if __name__ == "__main__":
    app.create_server(HOST, PORT)