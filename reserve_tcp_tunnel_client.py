#!/usr/bin/python3
# -*- coding: utf-8 -*-

import asyncio

#import hexdump

_CLIENT_CONNECTIONS = 1000


class Client:
    '''
    Reserve TCP tunnel client
    '''
    def __init__(self, tunnel_server_ip, tunnel_server_port, http_proxy_ip, http_proxy_port):
        self.__tunnel_server_ip = tunnel_server_ip
        self.__tunnel_server_port = tunnel_server_port
        self.__http_proxy_ip = http_proxy_ip
        self.__http_proxy_port = http_proxy_port

    async def __copy_data_ptoa56(self, info, p_reader5, a_writer6):
        addr = a_writer6.get_extra_info('peername')
        total = 0
        while True:
            chunk = await p_reader5.read(1024)
            if not chunk:
                break
            total += len(chunk)
            print("{0}:{1}".format(info, addr))
            #hexdump.hexdump(chunk[:32])
            a_writer6.write(chunk)
            await a_writer6.drain()
        print('5->6 {} done. total={}'.format(info, total))
        print("close sock[{0}]:{1}".format(info, addr))
        a_writer6.close()
        asyncio.ensure_future(self.tunnel_server_connection(1))

    async def __copy_data_atop34(self,
                                 info,
                                 a_reader3,
                                 a_writer6,
                                 p_reader5=None,
                                 p_writer4=None):
        addr = a_writer6.get_extra_info('peername')
        total = 0
        while True:
            chunk = await a_reader3.read(1024)
            if not chunk:
                assert total != 0
                break
            total += len(chunk)
            if p_reader5 == None:
                p_reader5, p_writer4 = await self._connect(
                    'http_proxy', self.__http_proxy_ip, self.__http_proxy_port)
                asyncio.ensure_future(
                    self.__copy_data_ptoa56('p->a', p_reader5, a_writer6))
            print("{0}:{1}".format(info, addr))
            #hexdump.hexdump(chunk[:32])
            p_writer4.write(chunk)
            await p_writer4.drain()
        print('3->4 {} done. total={}'.format(info, total))
        print("close sock[{0}]:{1}".format(info, addr))
        p_writer4.close()

    async def _connect(self, info, ip, port):
        print('try connection {} {}:{}'.format(info, ip, port))
        reader, writer = await asyncio.open_connection(ip, port)
        addr = writer.get_extra_info('peername')
        print("connection to[{0}]:{1}".format(info, addr))
        return reader, writer

    async def tunnel_server_connection(self, id):
        a_reader3, a_writer6 = await self._connect('tunnel_server',
                                                   self.__tunnel_server_ip,
                                                   self.__tunnel_server_port)
        task = asyncio.ensure_future(
            self.__copy_data_atop34('a->p',
                                    a_reader3,
                                    a_writer6,
                                    p_reader5=None,
                                    p_writer4=None))
        print('create_tunnel_server_connection id = {}'.format(id))


def main(tunnel_server_ip, tunnel_server_port, http_proxy_ip, http_proxy_port):
    tp = Client(tunnel_server_ip, tunnel_server_port, http_proxy_ip, http_proxy_port)
    loop = asyncio.get_event_loop()
    global _CLIENT_CONNECTIONS
    for i in range(_CLIENT_CONNECTIONS):
        asyncio.ensure_future(tp.tunnel_server_connection(i), loop=loop)
    while True:
        try:
            loop.run_forever()
        except ConnectionRefusedError as e:
            print('Connection to server {} failed!'.format(e))
        except asyncio.TimeoutError as e:
            print('Connection to server {} timed out!'.format(e))
        else:
            print('Connection to server {} is closed.'.format(tp))
        finally:
            pass
            asyncio.ensure_future(tp.tunnel_server_connection())


if __name__ == "__main__":
    server_ip = '127.0.0.1'
    server_port = 2222
    main(tunnel_server_ip=server_ip,
         tunnel_server_port=server_port,
         http_proxy_ip='127.0.0.1',
         http_proxy_port=8118)
