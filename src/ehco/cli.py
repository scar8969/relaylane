import argparse


def _models():
    """Import the ORM lazily.

    `python cli.py --help` must work on a machine that has not pip-installed
    flask-sqlalchemy, so the import lives inside the command that needs it
    instead of at module scope.
    """
    from .models import Tunnel, db

    return Tunnel, db


def cmd_tunnel_add(args):
    Tunnel, db = _models()
    from ._app import app

    with app.app_context():
        t = Tunnel(
            name=args.name,
            listen=args.listen,
            proto=args.proto,
            tls=1 if args.tls else 0,
            cert_path=args.cert or "",
        )
        db.session.add(t)
        db.session.commit()
        print(f"tunnel {t.name} listening {t.listen}")
    return 0


def main():
    p = argparse.ArgumentParser(prog="ehco")
    sub = p.add_subparsers(dest="cmd")
    t = sub.add_parser("tunnel")
    ts = t.add_subparsers(dest="sub")
    a = ts.add_parser("add")
    a.add_argument("name")
    a.add_argument("listen")
    a.add_argument("--proto", default="tcp", choices=("tcp", "udp"))
    a.add_argument("--tls", action="store_true")
    a.add_argument("--cert", default="")
    args = p.parse_args()
    if args.cmd == "tunnel" and args.sub == "add":
        return cmd_tunnel_add(args)
    p.print_help()
    return 1
