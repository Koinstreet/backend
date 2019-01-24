import asyncio
import websockets
import json
import requests


ws_url = 'wss://api.hitbtc.com/api/2/ws'
rs_url = 'https://api.hitbtc.com/api/2/public/'

methods = ['subscribeTicker','subscribeOrderbook','updateTrades','subscribeCandles']
tag = lambda x: x.replace('subscribe','')

class HitBtc:

    def __init__(self):
        self.tickers = [i['id'] for i in self.get_ticks()]

    def get_ticks(self):
        r = requests.get('{}{}'.format(rs_url,'symbol'))
        return r.json()

    def raw_msg(self, method='', symbol=''):
        return {"method":method,"params":{"symbol":symbol},"id":123} if method != 'subscribeCandles' else {"method":method,"params":{"symbol":symbol,"period":"M30","limit":1},"id": 123}



h = HitBtc()

async def Exchange():

    async with websockets.connect(ws_url) as ws:
        await ws.send(json.dumps(h.raw_msg(method='subscribeTicker', symbol='LTCTUSD')))
        while True:
            msg = await ws.recv()
            print(json.loads(msg))
        '''
        while True:
            for i in h.tickers:
                await asyncio.sleep(0.05)
                msg = h.raw_msg(method='subscribeTicker', symbol=i)
                await ws.send(json.dumps(msg))
                resp = await ws.recv()
                print('Ticker: {} | {}'.format(i,resp))
        '''

asyncio.get_event_loop().run_until_complete(Exchange())
