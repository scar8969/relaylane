import asyncio

class MuxSession:
    def __init__(self):
        self._streams = {}
        self._next = 1

    async def open_stream(self):
        sid = self._next; self._next += 1
        self._streams[sid] = asyncio.Queue()
        return sid

    async def close_stream(self, sid):
        self._streams.pop(sid, None)
