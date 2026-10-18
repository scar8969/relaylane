from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Tunnel(db.Model):
    __tablename__ = "tunnels"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    listen = db.Column(db.String(128), default="0.0.0.0:8443")
    proto = db.Column(db.String(8), default="tcp")  # tcp|udp
    tls = db.Column(db.Integer, default=0)
    cert_path = db.Column(db.String(256), default="")
    lb = db.Column(db.String(16), default="least-conn")  # round-robin|least-conn
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Upstream(db.Model):
    __tablename__ = "upstreams"
    id = db.Column(db.Integer, primary_key=True)
    tunnel_id = db.Column(db.Integer, db.ForeignKey("tunnels.id"))
    addr = db.Column(db.String(128), default="")
    weight = db.Column(db.Integer, default=1)
    healthy = db.Column(db.Integer, default=1)
    last_check = db.Column(db.DateTime, nullable=True)


class Stats(db.Model):
    __tablename__ = "stats"
    id = db.Column(db.Integer, primary_key=True)
    tunnel_id = db.Column(db.Integer, db.ForeignKey("tunnels.id"))
    bytes = db.Column(db.BigInteger, default=0)
    at = db.Column(db.DateTime, default=datetime.utcnow)
