import asyncio
import websockets
import ast
import time


async def hello(websocket, path):
    async for order in websocket:
        order = ast.literal_eval(order)
        greeting = "Recieved order : " + str(order)
        await websocket.send(str(greeting))
        print('API sent back response')


def start_server(bot_id):
    # asyncio.set_event_loop(asyncio.new_event_loop())
    server = websockets.serve(hello, 'localhost', bot_id + 1000)
    print('API server started, listening on ', bot_id + 1000)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    start_server(0)