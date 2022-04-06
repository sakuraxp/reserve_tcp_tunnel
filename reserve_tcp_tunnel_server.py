#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio

#import hexdump


class Server:
    '''
    Reserve TCP tunnel server
    '''
    def __init__(self):
        self._queue = asyncio.Queue()
        self.__proxy_count = 0

    async def __copy_data_ptoa12(self, info, p_reader1, p_writer2):
        addr = p_writer2.get_extra_info('peername')
        total = 0
        while True:
            chunk = await p_reader1.read(1024)
            if not chunk:
                break
            total += len(chunk)
            print("{0}:{1}".format(info, addr))
            #hexdump.hexdump(chunk[:32])
            p_writer2.write(chunk)
            await p_writer2.drain()
        print('1->2 {} done. total={}'.format(info, total))
        p_writer2.close()

    async def __copy_data_atop78(self, info, a_reader7, p_writer8):
        addr = p_writer8.get_extra_info('peername')
        total = 0
        while True:
            chunk = await a_reader7.read(1024)
            print('7->8 {}. total={}'.format(info, total))
            if not chunk:
                break
            total += len(chunk)
            print("{0}:{1}".format(info, addr))
            #hexdump.hexdump(chunk[:32])
            p_writer8.write(chunk)
            await p_writer8.drain()
        print('7->8 {} done. total={}'.format(info, total))
        print("close sock[{0}]:{1}".format(info, addr))
        p_writer8.close()

    async def tcp_tunnel_handle(self, a_reader7, a_writer2):
        '''
        处理tcp_tunnel_client -> tcp_tunnel_listener 的连接
        '''
        addr = a_writer2.get_extra_info('peername')
        print("[tunnel_client]to[tunnel_server]:{}".format(addr))
        await self._queue.put([a_reader7, a_writer2])
        #a_reader7.read(4)
        print("client_ready_connections count={}".format(self._queue.qsize()))

    async def local_proxy_handle(self, p_reader1, p_writer8):
        '''
        处理 server 端本地的的代理请求
        '''
        self.__proxy_count += 1
        addr = p_writer8.get_extra_info('peername')
        print("sock[{}]count{}:{}".format('localproxy', self.__proxy_count,
                                          addr))
        a_reader7, a_writer2 = await self._queue.get()
        asyncio.ensure_future(
            self.__copy_data_ptoa12('p->a', p_reader1, a_writer2))
        asyncio.ensure_future(
            self.__copy_data_atop78('a->p', a_reader7, p_writer8))


def main(tunnelListener, localProxyListener):
    tp = Server()
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(tp.tcp_tunnel_handle, *tunnelListener)
    server = loop.run_until_complete(coro)
    print('Serving on tcp_tunnel{}'.format(server.sockets[0].getsockname()))
    coro2 = asyncio.start_server(tp.local_proxy_handle, *localProxyListener)
    server2 = loop.run_until_complete(coro2)
    print('Serving on local_proxy{}'.format(server2.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    server.close()
    loop.run_until_complete(server.wait_closed())
    server2.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()


if __name__ == "__main__":
    main(tunnelListener=('0.0.0.0', 2222),
         localProxyListener=('0.0.0.0', 8080))
