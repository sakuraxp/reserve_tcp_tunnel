#!/usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio


class Reserve_TCP_Tunnel_Client:
    def __init__(self, ts_config, hp_config):
        self._ts_host, self._ts_port = ts_config
        self._hp_host, self._hp_port = hp_config

    async def _copy_data_pc56(self, info, p_reader5, a_writer6):
        addr = a_writer6.get_extra_info('peername')
        total = 0
        while True:
            chunk = await p_reader5.read(1024)
            if not chunk:
                break
            total += len(chunk)
            a_writer6.write(chunk)
            await a_writer6.drain()
        print(f"close sock[{info}]:{addr}, total send={total}.")
        a_writer6.close()
        asyncio.ensure_future(self.connect_tunnel_server())

    async def _copy_data_cp34(self, info, a_reader3, a_writer6):
        addr = a_writer6.get_extra_info('peername')
        total = 0
        while True:
            chunk = await a_reader3.read(1024)
            if not chunk:
                break

            if total == 0:
                print(f"open sock[tc->hp]: {self._hp_host}:{self._hp_port}")
                p_reader5, p_writer4 = await asyncio.open_connection(
                    self._hp_host, self._hp_port)
                asyncio.ensure_future(
                    self._copy_data_pc56('hp->tc', p_reader5, a_writer6))

            total += len(chunk)
            p_writer4.write(chunk)
            await p_writer4.drain()
        print(f"close sock[{info}]:{addr}, total send={total}.")
        p_writer4.close()

    async def connect_tunnel_server(self):
        a_reader3, a_writer6 = await asyncio.open_connection(
            self._ts_host, self._ts_port)
        task = asyncio.ensure_future(
            self._copy_data_cp34('tc->hp', a_reader3, a_writer6))

    def run(self, CONST_CLIENT_CONNECTIONS=500):
        loop = asyncio.get_event_loop()
        print(
            f"open sock[tunnel_server]: {self._ts_host}:{self._ts_port}, CONNECTIONS = {CONST_CLIENT_CONNECTIONS}"
        )
        for _ in range(CONST_CLIENT_CONNECTIONS):
            asyncio.ensure_future(client.connect_tunnel_server())

        while True:
            try:
                loop.run_forever()
            except ConnectionRefusedError as e:
                print('Connection to server {} failed!'.format(e))
            except asyncio.TimeoutError as e:
                print('Connection to server {} timed out!'.format(e))
            else:
                print('Connection to server {} is closed.'.format(client))
            finally:
                pass
                asyncio.ensure_future(client.connect_tunnel_server())


if __name__ == "__main__":
    ts_config = '127.0.0.1', 2222
    hp_config = '127.0.0.1', 8118
    CONST__CLIENT_CONNECTIONS = 500
    client = Reserve_TCP_Tunnel_Client(ts_config, hp_config)
    client.run(CONST_CLIENT_CONNECTIONS)
