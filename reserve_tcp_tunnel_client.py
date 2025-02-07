# reserve_tcp_tunnel_client.py
#!/usr/bin/python3
import asyncio

class TunnelClient:
    def __init__(self, ts_host, ts_port, proxy_host, proxy_port):
        self.ts_host = ts_host
        self.ts_port = ts_port
        self.proxy_host = proxy_host
        self.proxy_port = proxy_port
        self.connection_sem = asyncio.Semaphore(100)  # 并发控制
        self.max_connections = 200
        self.current_connections = 0
        self.lock = asyncio.Lock()

    async def maintain_connections(self):
        while True:
            async with self.lock:
                needed = self.max_connections - self.current_connections
                
            if needed > 0:
                print(f"Establishing {needed} new connections...")
                tasks = []
                for _ in range(needed):
                    tasks.append(asyncio.create_task(self.connect()))
                
                await asyncio.gather(*tasks)
            
            await asyncio.sleep(1)  # 每秒检查一次连接状态

    async def handle_server(self, reader, writer):
        async with self.connection_sem:
            try:
                proxy_reader, proxy_writer = await asyncio.open_connection(
                    self.proxy_host, self.proxy_port)
                
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
                    forward(reader, proxy_writer),
                    forward(proxy_reader, writer)
                )
            finally:
                async with self.lock:
                    self.current_connections -= 1

    async def connect(self):
        try:
            reader, writer = await asyncio.open_connection(
                self.ts_host, self.ts_port)
            async with self.lock:
                self.current_connections += 1
            await self.handle_server(reader, writer)
        except Exception as e:
            async with self.lock:
                self.current_connections -= 1
            await asyncio.sleep(0.1)

    def run(self):
        loop = asyncio.get_event_loop()
        # 启动连接维护任务
        loop.create_task(self.maintain_connections())
        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

if __name__ == "__main__":
    client = TunnelClient(
        ts_host="192.168.123.61",
        ts_port=2222,
        proxy_host="127.0.0.1",
        proxy_port=1080
    )
    client.run()
