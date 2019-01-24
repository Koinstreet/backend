import asyncio
import websockets
import time
import datetime

from binance import Binance
from coinbase import Coinbase
from bittrex import Bittrex

host = 'localhost'
port = 5678

loop = asyncio.get_event_loop()
curr_time = lambda: datetime.datetime.fromtimestamp(int(time.time())).strftime('%m-%d-%Y %H:%M:%S')

BINANCE = Binance(ohlc='1m', depth=5, ping=3, hours=23)
COINBASE = Coinbase()
BITTREX = Bittrex()

async def start(websocket, path):
    print('Opening Server @ {}'.format(curr_time()))
    tasks = [loop.create_task(BINANCE.start(loop, websocket)),
             loop.create_task(COINBASE.start(loop, websocket)),
             loop.create_task(BITTREX.start(loop, websocket))]
    await asyncio.wait(tasks)

def connection(loop, host='localhost', port=5678):
    server = websockets.serve(start, host, port)
    loop.run_until_complete(server)
    loop.run_forever()

if __name__ == '__main__':
    connection(loop, host=host, port=port)
