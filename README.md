<p align="center">
  <img src="docs/assets/screens/root.png" alt="relaylane running" width="900">
</p>

<h1 align="center">relaylane</h1>

<p align="center"><b>TCP and UDP relays with load balancing, managed over HTTP.</b></p>

<p align="center">
  <a href="#quality-gates"><img src="https://img.shields.io/badge/tests-25%20passed-2ea44f" alt="tests: 25 passed"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/coverage-57.4%-yellow" alt="coverage: 57.4%"></a> <a href="#api"><img src="https://img.shields.io/badge/routes-10%20answered-0969da" alt="routes: 10 answered"></a> <a href="#requirements"><img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="python: 3.11+"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="license: MIT"></a>
</p>

relaylane forwards TCP and UDP traffic from a listen address to a set of upstreams, picks one with least-connections or round-robin, and counts bytes per tunnel so a relay that is saturating is visible.

---

**Contents** &nbsp;·&nbsp; [Why](#why-this-exists) &nbsp;·&nbsp; [What it does](#what-it-does) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [API](#api) &nbsp;·&nbsp; [Screenshots](#screenshots) &nbsp;·&nbsp; [Measured](#measured-not-estimated) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Quality gates](#quality-gates) &nbsp;·&nbsp; [Deploy](#deploy) &nbsp;·&nbsp; [Limits](#limits-stated-rather-than-hidden)

## Why this exists

iptables DNAT is fine until you need two upstreams, health, or a byte count per customer. Doing the relay in the application makes the routing decision inspectable and the counters real.

## What it does

| Capability | How it works |
| --- | --- |
| **TCP and UDP** | Separate relay implementations with the same tunnel contract; UDP keeps a flow table. |
| **Load balancing** | Least-connections and round-robin over healthy upstreams only. |
| **Per-tunnel counters** | Bytes in and out per tunnel, reported by GET /api/stats. |
| **Runtime configuration** | Add tunnels and upstreams over HTTP or the CLI; the panel lists what is running. |

## Quickstart

```sh
git clone https://github.com/scar8969/relaylane.git
cd relaylane
python -m venv .venv && . .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
python wsgi.py                                 # http://127.0.0.1:8000
```

The same work from the CLI:

```sh
python -m ehco.cli --help
```

Commands: `tunnel`, `add`.

A first request:

```sh
curl -s http://127.0.0.1:8000/api/tunnels | head
```

## Requirements

- Python **3.11+** — CI runs 3.11, 3.12 and 3.13.
- Runtime dependencies: `Flask>=3.0`, `Flask-SQLAlchemy>=3.1`, `SQLAlchemy>=2.0`, `PyYAML>=6.0`.
- No JavaScript build step: every page is server-rendered Jinja.

## API

Every route below is in [`openapi/relaylane.yaml`](openapi/relaylane.yaml) and is exercised by the live probe recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/api/tunnels` | list |
| `POST` | `/api/upstreams` | add upstream |
| `GET` | `/api/stats` | stats |

## Screenshots

Captured from the running service with headless Chromium at 1440×900, one image per page, committed under [`docs/assets/screens/`](docs/assets/screens/).

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/tunnels-new.png" alt="/tunnels/new" width="100%"><br><sub><code>/tunnels/new</code> &middot; 25.0 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/healthz.png" alt="/healthz" width="100%"><br><sub><code>/healthz</code> &middot; 8.1 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/livez.png" alt="/livez" width="100%"><br><sub><code>/livez</code> &middot; 7.3 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/metrics.png" alt="/metrics" width="100%"><br><sub><code>/metrics</code> &middot; 14.8 KB</sub></td>
</tr>
</table>

<table>
<tr>
<td width="50%"><img src="docs/assets/screens/readyz.png" alt="/readyz" width="100%"><br><sub><code>/readyz</code> &middot; 7.7 KB</sub></td>
<td width="50%"><img src="docs/assets/screens/version.png" alt="/version" width="100%"><br><sub><code>/version</code> &middot; 25.0 KB</sub></td>
</tr>
</table>

## Measured, not estimated

These numbers were produced on this checkout by `pytest --cov` and by booting `wsgi.py` and issuing one real GET per documented path. The commands are in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Signal | Value |
| --- | --- |
| Tests | **25 / 25 passed** (6.0 s, exit 0) |
| Line coverage | **57.4%** — 442 of 734 statements |
| Source | 16 files / 1,555 lines |
| Test code | 4 files / 244 lines |
| Documented paths | 3 in the spec, 2 GET |
| Live probe | 11 GET requests to the booted app, **10 answered 200** |
| Median latency | **36.1 ms** (single uncached request, dev server) |
| Slowest / fastest | 198.8 ms `/healthz` / 4.2 ms `/version` |
| Bytes served | 13.2 KB across 11 responses |
| Screenshots | 7 captured |

## Architecture

```
relaylane/
├── src/ehco/
│   ├── http.py                         379  HTTP plumbing for ehco: correlation ids, access logs
│   ├── _app.py                         238  Web UI for ehco: tunnel/upstream management on top o
│   ├── config.py                       171  Environment-driven configuration for ehco
│   ├── observability.py                169  Structured logging and request correlation for ehco
│   ├── app.py                          119  Application factory for ehco
│   ├── errors.py                       108  Typed application errors and their HTTP mapping for 
│   ├── relay/tcp.py                     79  
│   ├── relay/api.py                     70  
│   ├── paths.py                         52  Filesystem layout for ehco
│   ├── cli.py                           50  
│   ├── relay/udp.py                     38  
│   ├── models.py                        36  
├── openapi/relaylane.yaml                 the contract of record
├── schema/relaylane.sql                   the DDL
├── tests/                       the suite that has to stay green
├── docs/EVIDENCE.md             the recorded live route walk
├── Dockerfile                   multi-stage build
└── wsgi.py                      entry point
```

The package keeps one shape across the service: `config.py` reads the environment once, `observability.py` emits structured JSON logs carrying a request id, `errors.py` turns exceptions into a single JSON envelope, `models.py` holds the tables, and the `relay/` package holds the routes.

## Quality gates

| Gate | Command | Threshold |
| --- | --- | --- |
| Suite | `pytest -q` | all green |
| Coverage | `pytest --cov` | floor set in `pyproject.toml` from the measured value |
| Lint | `ruff check src tests` | zero findings |
| Format | `ruff format --check src tests` | zero reformats |
| Types | `mypy src` | zero errors |
| Security | `bandit -c pyproject.toml -r src` | reviewed skip list, no unreviewed finding |
| Live routes | boot `wsgi.py`, one GET per documented path | no 5xx, no undocumented guard |

CI runs the first six on Python 3.11, 3.12 and 3.13 for every push to `main`, plus a container build. See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Deploy

```sh
docker build -t relaylane .
docker run --rm -p 8000:8000 --env-file .env.example relaylane
```

Configuration is environment-only — every variable is documented in [`.env.example`](.env.example), and the service refuses to start with a production secret missing.

## Limits, stated rather than hidden

- Upstream health is a passive flag, not an active probe.
- TLS termination is pass-through; certificate files are referenced but not reloaded on change.

## License

MIT — see [LICENSE](LICENSE).
