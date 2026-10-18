import asyncio
from typing import Any

from ..models import Tunnel


class UdpRelay:
    def __init__(self, tunnel: Tunnel, upstreams: list, on_bytes):
        self.tunnel = tunnel
        self.upstreams = upstreams
        self.on_bytes = on_bytes
        self.transport: Any = None

    async def start(self) -> None:
        loop = asyncio.get_running_loop()
        host, port = self.tunnel.listen.rsplit(":", 1)
        self.transport, _ = await loop.create_datagram_endpoint(
            lambda: _Proto(self), local_addr=(host, int(port))
        )
        return self.transport

    async def forward(self, packet) -> None:
        from .lb import LoadBalancer

        up = LoadBalancer(self.tunnel.lb).pick(self.upstreams)
        if up is None or self.transport is None:
            return
        host, port = up.addr.rsplit(":", 1)
        self.transport.sendto(packet, (host, int(port)))


class _Proto(asyncio.DatagramProtocol):
    def __init__(self, relay):
        self.relay = relay

    def datagram_received(self, data, addr):
        self.relay.on_bytes(len(data), True)
