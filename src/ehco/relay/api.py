from flask import Blueprint, jsonify, request

from ..models import Stats, Tunnel, Upstream, db

bp = Blueprint("relay", __name__)


@bp.post("/api/tunnels")
def add_tunnel():
    d = request.get_json(force=True, silent=True) or {}
    t = Tunnel(
        name=d.get("name", ""),
        listen=d.get("listen", "0.0.0.0:8443"),
        proto=d.get("proto", "tcp"),
        tls=1 if d.get("tls") else 0,
        cert_path=d.get("cert_path", ""),
        lb=d.get("lb", "least-conn"),
    )
    db.session.add(t)
    db.session.commit()
    return jsonify({"id": t.id})


@bp.get("/api/tunnels")
def list_tunnels():
    return jsonify(
        {
            "tunnels": [
                {
                    "id": t.id,
                    "name": t.name,
                    "listen": t.listen,
                    "proto": t.proto,
                    "upstreams": Upstream.query.filter_by(tunnel_id=t.id).count(),
                    "healthy": sum(
                        1 for u in Upstream.query.filter_by(tunnel_id=t.id, healthy=1).all()
                    ),
                    "bytes": sum(s.bytes for s in Stats.query.filter_by(tunnel_id=t.id).all()),
                }
                for t in Tunnel.query.all()
            ]
        }
    )


@bp.post("/api/upstreams")
def add_upstream():
    d = request.get_json(force=True, silent=True) or {}
    u = Upstream(tunnel_id=d.get("tunnel_id", 0), addr=d.get("addr", ""), weight=d.get("weight", 1))
    db.session.add(u)
    db.session.commit()
    return jsonify({"id": u.id})


@bp.get("/api/stats")
def stats():
    total = sum(s.bytes for s in Stats.query.all())
    return jsonify(
        {
            "total_bytes": total,
            "per_tunnel": [
                {
                    "tunnel": t.name,
                    "bytes": sum(s.bytes for s in Stats.query.filter_by(tunnel_id=t.id).all()),
                }
                for t in Tunnel.query.all()
            ],
        }
    )
