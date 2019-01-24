import websockets
import asyncio
import json
import requests
import time
import datetime


ws_url = 'wss://stream.binance.com:9443'
rs_url = 'https://www.binance.com/api/v1/'

curr_time = lambda: datetime.datetime.fromtimestamp(int(time.time())).strftime('%m-%d-%Y %H:%M:%S')
dt = lambda x, y, n: (y - x) / n

url_build = lambda y, tag: '{}/ws/{}'.format(ws_url, y[0].lower()) if tag == 'single' else '{}/stream?streams={}'.format(ws_url, '/'.join(y))

sstream = {'aggTrade':lambda symbol: '{}@aggTrade'.format(symbol.lower()),
           'trade':lambda symbol: '{}@trade'.format(symbol.lower()),
           'klines':lambda symbol, interval: '{}@kline_{}'.format(symbol.lower(), interval),
           'miniTick':lambda symbol, all_t: '{}@miniTicker'.format(symbol.lower()) if all_t == False else '!miniTicker@arr',
           'ticker':lambda symbol, all_t: '{}@ticker'.format(symbol.lower()) if all_t == False else '!ticker@arr',
           'book':lambda symbol, level: '{}@depth'.format(symbol.lower()) if level == 'update' else '{}@depth{}'.format(symbol.lower(), level)}

stream_keys = sstream.keys()


class Binance:

    def __init__(self, ohlc=str, depth=int, ping=int, hours=int):

        self.init_time()

        self.params = [ohlc, depth, ping, hours]
        self.tickers = self.get_data('ticks')[:10]

    # Initializes and resets timestamp counters

    def init_time(self):
        self.tPing = {i:time.time() for i in stream_keys}
        self.tPong = {i:time.time() for i in stream_keys}
        self.tStart = {i:time.time() for i in stream_keys}
        self.tEnd = {i:time.time() for i in stream_keys}

    # Non asynchronus pre-parsing functions

    def get_data(self, datatype):
        if datatype == 'ticks':
            url = rs_url + 'exchangeInfo'
            r = requests.get(url)
            if r.status_code == 200:
                return [i['symbol'] for i in r.json()['symbols']]

    def stream(self, tag, ticks):
        if tag == 'klines':
            return [sstream['klines'](i, ticks[1]) for i in ticks[0]]
        elif tag == 'book':
            return [sstream['book'](i, ticks[1]) for i in ticks[0]]
        elif tag == 'trade':
            return [sstream['trade'](i) for i in ticks[0]]
        elif tag == 'ticker':
            return [sstream['ticker'](i, False) for i in ticks[0]]
        else:
            return [sstream['aggTrade'](i) for i in ticks[0]]

    def build_msg(self, tagger):
        msg = self.stream(tagger[0],[self.tickers,tagger[1]])
        return url_build(msg, 'multi')

    # Builds parameter lists and opens the initial connection

    async def start(self, loop, conn):
        items = [['klines',self.params[0]],['book',self.params[1]],['trade',None],['ticker',False],['aggTrade',None]]
        self.count = {i[0]:0 for i in items}
        tasks = [loop.create_task(self.exchange_client(conn, i)) for i in items]
        await asyncio.wait(tasks)

    # Main function which runs each exchange client

    async def exchange_client(self, conn, tagger):

        send_url = self.build_msg(tagger)

        tag = tagger[0] # Data type tag

        self.tPing[tag] = time.time()
        self.tStart[tag] = time.time()

        print('Exchange: Binance | Connection to {} has opened'.format(tag))

        async with websockets.connect(send_url) as ws:
            while True:
                try:
                    msg = await ws.recv()
                    await self.parse_data(conn, msg, tagger)

                    # Every 3 minutes the client sends a pong request

                    if dt(self.tPing[tag], self.tPong[tag], 60) >= self.params[2]:
                        await ws.pong()
                        print(' Time: {} | Pong Sent: {}'.format(curr_time(), ws.recv()))
                        await asyncio.sleep(3)
                        self.tPing[tag] = time.time()
                        self.tPong[tag] = time.time()

                    # Every 23 hours the client restarts its connection according to Binance rules

                    if dt(self.tStart[tag], self.tEnd[tag], pow(60, 2) * 24) >= self.params[3]:
                        print('Connection to {} has closed'.format(tag))
                        await asyncio.sleep(10)
                        self.init_time()
                        await self.exchange_client(conn, tagger)

                    await ws.ping()
                    self.tEnd[tag] = time.time()
                    self.tPong[tag] = time.time()

                except Exception as e:
                    print('Client error in {} | {}'.format(tag,e))
                    asyncio.sleep(10)
                    print('Rebooting {}'.format(tag))
                    self.count[tag] += 1
                    if self.count[tag] < 3:
                        self.exchange_client(conn, tagger)
                    else:
                        print('Binance | {} has ended'.foramt(tag))
                    
    # Parses data, creates and sends a tagged server message

    async def parse_data(self, conn, data, tagger):
        data = json.loads(data)
        #msg = ' Timestamp: {} | Tag: {} | {}\n'.format(curr_time(), tagger[0], data)
        message = {'Exchange':'Binance','Tag':tagger[0],'Data':data}
        await conn.send(json.dumps(message))
