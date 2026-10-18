"""A12 ehco — tests. Run: pytest test_relaylane.py"""
import sys, os

import pytest

class FakeUp:
    def __init__(self, id, healthy=True):
        self.id, self.healthy = id, healthy

def test_lb_round_robin():
    from ehco.relay.lb import LoadBalancer
    lb = LoadBalancer("round-robin")
    ups = [FakeUp(1), FakeUp(2)]
    picks = [lb.pick(ups).id for _ in range(4)]
    assert picks == [1, 2, 1, 2]

def test_lb_skips_unhealthy():
    from ehco.relay.lb import LoadBalancer
    lb = LoadBalancer("round-robin")
    ups = [FakeUp(1, healthy=False), FakeUp(2)]
    assert lb.pick(ups).id == 2

def test_lb_least_conn():
    from ehco.relay.lb import LoadBalancer
    lb = LoadBalancer("least-conn")
    ups = [FakeUp(1), FakeUp(2)]
    lb._conns[1] = 5
    assert lb.pick(ups).id == 2

def test_lb_no_healthy():
    from ehco.relay.lb import LoadBalancer
    lb = LoadBalancer()
    assert lb.pick([FakeUp(1, healthy=False)]) is None

def test_health_check():
    from ehco.relay.lb import health_check
    assert not health_check("127.0.0.1:1")
