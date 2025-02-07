# reserve_tcp_tunnel_server.py
#!/usr/bin/python3
import asyncio

class TunnelServer:
    def __init__(self, tunnel_port, proxy_port):
        self.tunnel_port = tunnel_port
        self.proxy_port = proxy_port
        self.connections = asyncio.Queue()

    async def handle_tunnel(self, reader, writer):
        await self.connections.put((reader, writer))

    async def handle_proxy(self, client_reader, client_writer):
        try:
            server_reader, server_writer = await self.connections.get()
            
            async def forward(src, dst):
                try:
                    while True:
                        data = await src.read(4096)
                        if not data:
                            break
                        dst.write(data)
                        await dst.drain()
                finally:
                    dst.close()

            await asyncio.gather(
                forward(client_reader, server_writer),
                forward(server_reader, client_writer)
            )
        finally:
            server_writer.close()

    def run(self):
        loop = asyncio.get_event_loop()
        
        tunnel_server = asyncio.start_server(
            self.handle_tunnel, '0.0.0.0', self.tunnel_port)
        proxy_server = asyncio.start_server(
            self.handle_proxy, '0.0.0.0', self.proxy_port)
        
        loop.run_until_complete(asyncio.gather(
            tunnel_server,
            proxy_server
        ))
        
        print(f"Tunnel server listening on {self.tunnel_port}")
        print(f"Proxy server listening on {self.proxy_port}")
        loop.run_forever()

if __name__ == "__main__":
    server = TunnelServer(
        tunnel_port=2222,
        proxy_port=8080
    )
    server.run()
