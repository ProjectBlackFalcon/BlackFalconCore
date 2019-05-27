import asyncio
import websockets
import ast
import time


async def hello(websocket, path):
    order = await websocket.recv()
    order = ast.literal_eval(order.decode('utf8'))
    greeting = "Recieved order : " + str(order)
    while 1:
        await websocket.send('A result')
        time.sleep(1)

def start_server(bot_id):
    asyncio.set_event_loop(asyncio.new_event_loop())
    server = websockets.serve(hello, 'localhost', bot_id + 1000)
    print('API server started, listening on ', bot_id + 1000)
    asyncio.get_event_loop().run_until_complete(server)
    asyncio.get_event_loop().run_forever()