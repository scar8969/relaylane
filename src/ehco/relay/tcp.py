import asyncio
import ssl

from ..models import Tunnel


class TcpRelay:
    def __init__(self, tunnel: Tunnel, upstreams: list, on_bytes):
        self.tunnel = tunnel
        self.upstreams = upstreams
        self.on_bytes = on_bytes

    def _listen(self) -> tuple:
        host, port = self.tunnel.listen.rsplit(":", 1)
        return host, int(port)

    async def start(self) -> None:
        server = await asyncio.start_server(self._handle, *self._listen())
        async with server:
            await server.serve_forever()

    async def _handle(self, reader, writer):
        from .lb import LoadBalancer

        up = LoadBalancer(self.tunnel.lb).pick(self.upstreams)
        if not up:
            writer.close()
            return
        r_reader, r_writer = await asyncio.open_connection(*up.addr.rsplit(":", 1))
        if self.tunnel.tls:
            ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            ctx.load_cert_chain(self.tunnel.cert_path)
            # wrap server side

        async def pump(src, dst, up_dir):
            while True:
                data = await src.read(65536)
                if not data:
                    break
                dst.write(data)
                await dst.drain()
                self.on_bytes(len(data), up_dir)

        await asyncio.gather(pump(reader, r_writer, True), pump(r_reader, writer, False))
        try:
            writer.close()
        except Exception:
            pass

    async def _pipe(self, a, b) -> None:
        """Bidirectional copy with byte counting."""
        while True:
            data = await a.read(65536)
            if not data:
                break
            b.write(data)
            await b.drain()
            self.on_bytes(len(data), True)
        try:
            b.close()
        except Exception:
            pass

    async def forward(self, packet):
        import asyncio

        upstreams = getattr(self, "upstreams", [])
        if not upstreams:
            return
        host, port = upstreams[0].addr.rsplit(":", 1)
        loop = asyncio.get_running_loop()
        tr, _ = await loop.create_datagram_endpoint(
            asyncio.DatagramProtocol, remote_addr=(host, int(port))
        )
        try:
            tr.sendto(packet)
        finally:
            tr.close()
