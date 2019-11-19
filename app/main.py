import asyncio
import os

from sanic import Sanic

from app.views import index, configurate

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')


app = Sanic()

app.add_route(index, '/')
app.add_route(configurate, '/configurate', methods=['POST'])

if __name__ == "__main__":
    server = app.create_server(HOST,
                               PORT,
                               debug=False,
                               access_log=False,
                               return_asyncio_server=True)
    loop = asyncio.get_event_loop()
    task = asyncio.ensure_future(server)
    loop.run_forever()
