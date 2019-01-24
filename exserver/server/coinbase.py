import websockets
import asyncio
import json
import requests
import time
import datetime

ws_url = 'wss://ws-feed.pro.coinbase.com'
rs_url = 'https://api.pro.coinbase.com'

curr_time = lambda: datetime.datetime.fromtimestamp(int(time.time())).strftime('%m-%d-%Y %H:%M:%S')

class Coinbase:

    def __init__(self):
        self.ticks = self.get_ticks()

    def get_ticks(self):
        r = requests.get('{}/{}'.format(rs_url, 'products'))
        return [i['id'] for i in r.json()]


    async def start(self, loop, conn):
        attributes = {'ticker':{"type": "subscribe",
                                "channels":[{"name":"ticker","product_ids":self.ticks}]
                               },
                      'book':{"type": "subscribe",
                                "channels":[{"name":"level2","product_ids":self.ticks}]
                               },
                      'match':{"type": "subscribe",
                                "channels":[{"name":"matches","product_ids":self.ticks}]
                               },
                      'full':{"type": "subscribe",
                                "channels":[{"name":"full","product_ids":self.ticks}]
                               }
                      }

        self.count = {i:0 for i in attributes.keys()}
        tasks = [loop.create_task(self.exchange_client(conn, i, j)) for i, j in attributes.items()]
        await asyncio.wait(tasks)

    async def exchange_client(self, conn, tag, msg):
        print('Exchange: Coinbase | Connection to {} has opened'.format(tag))
        
        async with websockets.connect(ws_url) as ws:
            await ws.send(json.dumps(msg))

            while True:
                try:
                    msg = await ws.recv()
                    await self.parse_data(conn, tag, msg)
                except Exception as e:
                    print('Client error in {} | {}'.format(tag, e))
                    asyncio.sleep(10)
                    print('Rebooting {}'.format(tag))
                    self.count[tag] += 1
                    if self.count[tag] <= 3:
                        self.exchange_client(conn, tag, msg)
                    else:
                        print('Coinbase | {} has ended'.format(tag))
                        break
                    
    async def parse_data(self, conn, tag, data):
        data = json.loads(data)
        msg = ' Timestamp: {} | Tag: {} | {}\n'.format(curr_time(), tag, data)
        message = {'Exchange':'Coinbase','Tag':tag,'Data':data}
        await conn.send(json.dumps(message))

