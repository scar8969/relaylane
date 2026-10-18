"""Web UI for ehco: tunnel/upstream management on top of the relay API.

Flask resolves `template_folder` relative to `app.root_path`, which is this
package directory (web/), while the templates live one level up in the project
root.  The path below is absolute and derived from this module's own file, so
the lookup is correct no matter which directory the process was started from.
"""

import os
from datetime import datetime

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for

from . import paths
from .models import Stats, Tunnel, Upstream, db
from .relay.api import bp

APP_NAME = "U0001f517 ehco"
PROTOS = ("tcp", "udp")
LB_MODES = ("least-conn", "round-robin")


def build_app():
    """Build the application: configuration, database, then routes."""
    app = Flask(
        __name__, template_folder=str(paths.TEMPLATES_DIR), instance_path=str(paths.INSTANCE_DIR)
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(paths.INSTANCE_DIR / "ehco.db")
    db.init_app(app)
    with app.app_context():
        paths.ensure_runtime_dirs()
        db.create_all()
    app.register_blueprint(bp)

    def _parse_addr(raw):
        """Split "host:port" into a (host, port) pair, or raise ValueError.

        A relay target with a malformed address is useless, so the form rejects it
        here instead of storing a row that would fail every health check.
        """
        text = (raw or "").strip()
        if ":" not in text:
            raise ValueError("address must be host:port")
        host, _, port = text.rpartition(":")
        if not host:
            raise ValueError("address must name a host")
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            raise ValueError("port must be 1-65535")
        return host, int(port)

    def _healthy_count(tunnel_id):
        return Upstream.query.filter_by(tunnel_id=tunnel_id, healthy=1).count()

    def _tunnel_bytes(tunnel_id):
        return sum(s.bytes or 0 for s in Stats.query.filter_by(tunnel_id=tunnel_id).all())

    def _page_context(**extra):
        ctx = {
            "app_name": APP_NAME,
            "tunnel_count": Tunnel.query.count(),
            "upstream_count": Upstream.query.count(),
            "healthy_count": Upstream.query.filter_by(healthy=1).count(),
            "total_bytes": sum(s.bytes or 0 for s in Stats.query.all()),
            "protos": PROTOS,
            "lb_modes": LB_MODES,
        }
        ctx.update(extra)
        return ctx

    @app.get("/")
    def index():
        tunnels = []
        for t in Tunnel.query.order_by(Tunnel.id).all():
            tunnels.append(
                {
                    "t": t,
                    "upstreams": Upstream.query.filter_by(tunnel_id=t.id).count(),
                    "healthy": _healthy_count(t.id),
                    "bytes": _tunnel_bytes(t.id),
                }
            )
        return render_template(
            "index.html", routes=_app_routes(), tunnels=tunnels, **_page_context()
        )

    @app.get("/tunnels/new")
    def add_form():
        return render_template("add.html", form={}, **_page_context())

    @app.post("/tunnels/new")
    def create_tunnel():
        form = {
            k: request.form.get(k, "").strip()
            for k in ("name", "listen", "proto", "lb", "cert_path")
        }
        form["tls"] = bool(request.form.get("tls"))
        errors = []
        if not form["name"]:
            errors.append("name is required")
        elif Tunnel.query.filter_by(name=form["name"]).first() is not None:
            errors.append("a tunnel named %s already exists" % form["name"])
        if form["proto"] not in PROTOS:
            errors.append("proto must be one of %s" % ", ".join(PROTOS))
        if form["lb"] not in LB_MODES:
            errors.append("load balancing must be one of %s" % ", ".join(LB_MODES))
        try:
            _parse_addr(form["listen"])
        except ValueError as exc:
            errors.append("listen: %s" % exc)
        if form["tls"] and not form["cert_path"]:
            errors.append("TLS needs a certificate path")
        if errors:
            for msg in errors:
                flash(msg, "error")
            return render_template("add.html", form=form, **_page_context()), 400
        t = Tunnel(
            name=form["name"],
            listen=form["listen"],
            proto=form["proto"],
            tls=1 if form["tls"] else 0,
            cert_path=form["cert_path"],
            lb=form["lb"],
        )
        db.session.add(t)
        db.session.commit()
        flash("tunnel %s created" % t.name, "success")
        return redirect(url_for("tunnel_detail", tid=t.id))

    @app.get("/tunnels/<int:tid>")
    def tunnel_detail(tid):
        t = db.session.get(Tunnel, tid)
        if t is None:
            return render_template("404.html", missing="tunnel %d" % tid, **_page_context()), 404
        upstreams = Upstream.query.filter_by(tunnel_id=t.id).order_by(Upstream.id).all()
        history = Stats.query.filter_by(tunnel_id=t.id).order_by(Stats.id.desc()).limit(20).all()
        return render_template(
            "tunnel.html",
            tunnel=t,
            upstreams=upstreams,
            history=history,
            bytes_total=_tunnel_bytes(t.id),
            **_page_context(),
        )

    @app.post("/tunnels/<int:tid>/delete")
    def delete_tunnel(tid):
        t = db.session.get(Tunnel, tid)
        if t is None:
            flash("tunnel %d is gone" % tid, "error")
            return redirect(url_for("index"))
        Stats.query.filter_by(tunnel_id=t.id).delete()
        Upstream.query.filter_by(tunnel_id=t.id).delete()
        db.session.delete(t)
        db.session.commit()
        flash("tunnel %s deleted" % t.name, "success")
        return redirect(url_for("index"))

    @app.post("/tunnels/<int:tid>/upstreams")
    def add_upstream(tid):
        t = db.session.get(Tunnel, tid)
        if t is None:
            flash("tunnel %d is gone" % tid, "error")
            return redirect(url_for("index"))
        addr = request.form.get("addr", "").strip()
        weight = request.form.get("weight", "1").strip() or "1"
        try:
            _parse_addr(addr)
        except ValueError as exc:
            flash("upstream: %s" % exc, "error")
            return redirect(url_for("tunnel_detail", tid=tid))
        if not weight.isdigit() or int(weight) < 1:
            flash("weight must be a positive integer", "error")
            return redirect(url_for("tunnel_detail", tid=tid))
        db.session.add(Upstream(tunnel_id=t.id, addr=addr, weight=int(weight), healthy=1))
        db.session.commit()
        flash("upstream %s added" % addr, "success")
        return redirect(url_for("tunnel_detail", tid=tid))

    @app.post("/tunnels/<int:tid>/upstreams/<int:uid>/check")
    def check_upstream(tid, uid):
        from .relay.lb import health_check

        u = db.session.get(Upstream, uid)
        if u is None or u.tunnel_id != tid:
            flash("upstream %d is gone" % uid, "error")
            return redirect(url_for("tunnel_detail", tid=tid))
        u.healthy = 1 if health_check(u.addr) else 0
        u.last_check = datetime.utcnow()
        db.session.commit()
        flash(
            "%s is %s" % (u.addr, "reachable" if u.healthy else "unreachable"),
            "success" if u.healthy else "error",
        )
        return redirect(url_for("tunnel_detail", tid=tid))

    @app.post("/tunnels/<int:tid>/upstreams/<int:uid>/delete")
    def delete_upstream(tid, uid):
        u = db.session.get(Upstream, uid)
        if u is None or u.tunnel_id != tid:
            flash("upstream %d is gone" % uid, "error")
        else:
            db.session.delete(u)
            db.session.commit()
            flash("upstream %s removed" % u.addr, "success")
        return redirect(url_for("tunnel_detail", tid=tid))

    @app.get("/api/health")
    def api_health():
        """Liveness plus the relay's own view of its upstreams."""
        upstreams = Upstream.query.all()
        return jsonify(
            {
                "status": "ok",
                "tunnels": Tunnel.query.count(),
                "upstreams": len(upstreams),
                "healthy": sum(1 for u in upstreams if u.healthy),
                "bytes": sum(s.bytes or 0 for s in Stats.query.all()),
            }
        )

    def _app_routes():
        """Every registered GET/HEAD rule, for the index page route table."""
        rows = []
        for rule in sorted(app.url_map.iter_rules(), key=lambda r: str(r)):
            methods = sorted(m for m in rule.methods if m in ("GET", "POST"))
            rows.append(
                {"rule": str(rule), "endpoint": rule.endpoint, "methods": ", ".join(methods)}
            )
        return rows

    if __name__ == "__main__":
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))

    return app


app = build_app()
