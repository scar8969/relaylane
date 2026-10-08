== curl ==
# POST /api/tunnels  {"name":"web-tls","listen":"0.0.0.0:8443","proto":"tcp","tls":true,"lb":"least-conn"}
# POST /api/upstreams  {"tunnel_id":1,"addr":"127.0.0.1:8001","weight":2}
# GET  /api/tunnels
# GET  /api/stats
# CLI: ehco tunnel add web-tls 0.0.0.0:8443 --proto tcp --tls --cert ./cert.pem

== session plan ==
# Session 1: tcp relay loopback → tests
# Session 2: TLS + mux → tests
# Session 3: lb + health checks → tests
# Session 4: web dashboard + cli → screenshots → README → CI/Docker/Pages → tag
