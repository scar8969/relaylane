import socket

def health_check(addr, proto="tcp"):
    host, port = addr.rsplit(":", 1)
    try:
        with socket.create_connection((host, int(port)), timeout=3):
            return True
    except Exception:
        return False

class LoadBalancer:
    def __init__(self, mode: str = "least-conn"):
        self.mode = mode
        self._conns = {}
        self._rr = 0

    def pick(self, upstreams):
        healthy = [u for u in upstreams if u.healthy]
        if not healthy:
            return None
        if self.mode == "round-robin":
            u = healthy[self._rr % len(healthy)]
            self._rr += 1
            return u
        # least-conn
        return min(healthy, key=lambda u: self._conns.get(u.id, 0))
