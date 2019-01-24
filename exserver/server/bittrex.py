from signalr_aio import Connection
from base64 import b64decode
from zlib import decompress, MAX_WBITS
import json
import asyncio
import requests

ws_url = 'https://socket.bittrex.com/signalr'
rs_url = 'https://api.bittrex.com/api/v1.1/public/'

sstream = {'ExchangeDelta':('SubscribeToExchangeDeltas','uE'),
           'SummaryDelta':('SubscribeToSummaryDeltas','uS'),
           'QueryExchange':('queryExchangeState',None)}#,
           #'QuerySummary':('querySummaryState',None)}#,
           #'SummaryLite':('SubscribeToSummaryLiteDeltas','uL')}

stream_keys = sstream.keys()

tagger = lambda x: 'ExchangeDelta' if 'Z' in x.keys() else 'SummaryDelta' if 'D' in x.keys() else 'Book'

class Bittrex:

    def __init__(self):
        self.conn = None
        self.tickers = self.get_ticks()

    def get_ticks(self):
        url = '{}{}'.format(rs_url, 'getmarkets')
        resp = requests.get(url)
        return resp.json()

    async def start(self, loop, conn):
        self.conn = conn
        self.count = {i:0 for i in stream_keys}
        tasks = [loop.create_task(self.exchange_client(loop, i)) for i in stream_keys]
        await asyncio.wait(tasks)

    async def exchange_client(self, loop, tag):
        print('Exchange: Bittrex | Connection to {} has opened'.format(sstream[tag]))
        connection = Connection(ws_url, session=None, loop=loop)
        hub = connection.register_hub('c2')

        connection.received += self.on_debug
        connection.error += self.on_error

        if sstream[tag][1]:
            hub.client.on(sstream[tag][1], self.parse_data)

        if tag != 'SummaryDelta':
            for i in self.tickers:
                hub.server.invoke(sstream[tag][0], i)
        else:
            hub.server.invoke(sstream[tag][0])

        
        #hub.server.invoke('SubscribeToSummaryDeltas')
        #hub.server.invoke('queryExchangeState', 'BTC-NEO')

        connection.start()

    async def parse_data(self, msg):
        msg = await self.process_message(msg[0])
        message = {'Exchange':'Bittrex','Data':msg}
        message['Tag'] = tagger(msg)
        await self.conn.send(json.dumps(message))

    async def on_debug(self, **msg):
        if 'R' in msg and type(msg['R']) is not bool:
            decoded_msg = await self.process_message(msg['R'])
            message = {'Exchange':'Bittrex','Data':msg}
            message['Tag'] = tagger(msg)
            await self.conn.send(json.dumps(message))

    async def on_error(self, msg):
        message = {'Exchange':'Bittrex','Data':msg}
        message['Tag'] = tagger(msg)
        await self.conn.send(json.dumps(message))

    async def process_message(self, message):
        try:
            deflated_msg = decompress(b64decode(message, validate=True), -MAX_WBITS)
        except SyntaxError as e:
            deflated_msg = decompress(b64decode(message, validate=True))
        except TypeError:
            deflated_msg = decompress(b64decode(message), -MAX_WBITS)
        return json.loads(deflated_msg.decode())
