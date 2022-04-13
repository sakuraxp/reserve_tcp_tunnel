#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio


class Reserve_TCP_Tunnel_Server:
    def __init__(self, ts_config, lp_config):
        self._ts_host, self._ts_port = ts_config
        self._lp_host, self._lp_port = lp_config
        self._queue = asyncio.Queue()

    async def _copy_data(self, info, reader, writer):
        addr = writer.get_extra_info('peername')
        total = 0
        while True:
            chunk = await reader.read(1024)
            if not chunk:
                break
            total += len(chunk)
            writer.write(chunk)
            await writer.drain()
        print(f"close sock[{info}]:{addr}, total send={total}.")
        writer.close()

    async def _tunnel_handle(self, c_reader7, c_writer2):
        '''处理 tunnel_client -> tunnel_server 的连接 '''
        await self._queue.put([c_reader7, c_writer2])
        addr = c_writer2.get_extra_info('peername')
        print(f"open sock[c->s]:{addr}, connected:{self._queue.qsize()}")

    async def _proxy_handle(self, s_reader1, s_writer8):
        '''处理 server 端本地的的代理请求'''
        addr = s_writer8.get_extra_info('peername')
        print(f"open sock[localproxy]: {addr}")
        c_reader7, c_writer2 = await self._queue.get()
        asyncio.ensure_future(self._copy_data('s->c', s_reader1, c_writer2))
        asyncio.ensure_future(self._copy_data('c->s', c_reader7, s_writer8))

    def run(self):
        loop = asyncio.get_event_loop()
        ts_coro = asyncio.start_server(self._tunnel_handle, self._ts_host,
                                       self._ts_port)
        ts_loop = loop.run_until_complete(ts_coro)
        print('Serving for tunnel {}'.format(ts_loop.sockets[0].getsockname()))
        lp_coro = asyncio.start_server(self._proxy_handle, self._lp_host,
                                       self._lp_port)
        lp_loop = loop.run_until_complete(lp_coro)
        print('Serving on localProxy {}'.format(
            lp_loop.sockets[0].getsockname()))
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        ts_loop.close()
        loop.run_until_complete(ts_loop.wait_closed())
        lp_loop.close()
        loop.run_until_complete(lp_loop.wait_closed())
        loop.close()


if __name__ == "__main__":
    ts = Reserve_TCP_Tunnel_Server(ts_config=('0.0.0.0', 2222),
                                   lp_config=('0.0.0.0', 8080))
    ts.run()
