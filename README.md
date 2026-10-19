<p align="center">
  <img src="docs/assets/screens/root.png" alt="relaylane running" width="900">
</p>

<h1 align="center">relaylane</h1>

<p align="center"><b>TCP and UDP relays with load balancing, managed over HTTP.</b></p>

<p align="center">
  <a href="https://github.com/scar8969/relaylane/actions/workflows/ci.yml"><img src="https://github.com/scar8969/relaylane/actions/workflows/ci.yml/badge.svg" alt="ci"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/tests-25%20passed-2ea44f" alt="tests: 25 passed"></a> <a href="#quality-gates"><img src="https://img.shields.io/badge/coverage-57.4%-yellow" alt="coverage: 57.4%"></a> <a href="#api"><img src="https://img.shields.io/badge/routes-10%20live-0969da" alt="routes: 10 live"></a> <a href="#requirements"><img src="https://img.shields.io/badge/python-3.11%2B-3776ab" alt="python: 3.11+"></a> <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-2ea44f" alt="license: MIT"></a>
</p>

relaylane forwards TCP and UDP traffic from a listen address to a set of upstreams, picks one with least-connections or round-robin, and counts bytes per tunnel so a relay that is saturating is visible.

---

**Contents** &nbsp;·&nbsp; [Why](#why-this-exists) &nbsp;·&nbsp; [What it does](#what-it-does) &nbsp;·&nbsp; [Quickstart](#quickstart) &nbsp;·&nbsp; [Screenshots](#screenshots) &nbsp;·&nbsp; [API](#api) &nbsp;·&nbsp; [CLI](#cli) &nbsp;·&nbsp; [Configuration](#configuration) &nbsp;·&nbsp; [Measured](#measured-not-estimated) &nbsp;·&nbsp; [How a request flows](#how-a-request-flows) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [Quality gates](#quality-gates) &nbsp;·&nbsp; [Development](#development) &nbsp;·&nbsp; [Deploy](#deploy) &nbsp;·&nbsp; [Limits](#limits-stated-rather-than-hidden)

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

It is up when this answers:

```sh
curl -s http://127.0.0.1:8000/api/tunnels
```

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

## API

Every route below is declared in [`openapi/relaylane.yaml`](openapi/relaylane.yaml) and exercised by the live probe recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Method | Path | What it does |
| --- | --- | --- |
| `GET` | `/api/tunnels` | list |
| `POST` | `/api/tunnels` | add tunnel |
| `POST` | `/api/upstreams` | add upstream |
| `GET` | `/api/stats` | stats |

## CLI

The same operations without an HTTP client. Installed as `relaylane`, and runnable from a checkout with no install:

```sh
python -m ehco.cli --help
```

```text
usage: ehco [-h] {tunnel} ...

positional arguments:
  {tunnel}

options:
  -h, --help  show this help message and exit
```

## Configuration

Environment only — there is no config file. Copy `.env.example` to `.env` and edit; `APP_ENV=production` refuses to start without `SECRET_KEY`.

| Variable | Default | Meaning |
| --- | --- | --- |
| `APP_ENV` | `development` | development \| staging \| production; production enforces the secret. |
| `SECRET_KEY` | `change-me-in-production` | Session/CSRF signing key. Required when APP_ENV=production. |
| `HOST` | `0.0.0.0` | Interface the dev server binds. |
| `PORT` | `8000` | Port the dev server and the container listen on. |
| `DEBUG` | `false` | Flask debug mode. Never true in production. |
| `MAX_CONTENT_LENGTH` | `8388608` | Largest accepted request body, in bytes. |
| `DATA_DIR` | `(empty)` | Where uploaded and generated files live. |
| `INSTANCE_DIR` | `(empty)` | Where the SQLite file and instance state live. |
| `LOG_DIR` | `(empty)` | Where rotated log files are written, if file logging is on. |
| `LOG_LEVEL` | `INFO` | DEBUG \| INFO \| WARNING \| ERROR. |
| `LOG_JSON` | `true` | true emits one JSON object per line; false is human-readable. |
| `REQUEST_ID_HEADER` | `X-Request-ID` | Header echoed on every response and stamped on every log line. |

## Measured, not estimated

Produced on this checkout by `pytest --cov` and by booting `wsgi.py` and issuing one real GET per documented path. The commands are recorded in [`docs/EVIDENCE.md`](docs/EVIDENCE.md).

| Signal | Value |
| --- | --- |
| Tests | **25 / 25 passed** (3.8 s, exit 0) |
| Line coverage | **57.4%** — 442 of 734 statements |
| Source | 16 files / 1,574 lines |
| Test code | 4 files / 244 lines |
| Documented paths | 3 in the spec, 2 GET |
| Live probe | 11 GET requests to the booted app, **10 answered 200** |
| Median latency | **36.1 ms** (single uncached request, dev server) |
| Slowest / fastest | 198.8 ms `/healthz` / 4.2 ms `/version` |
| Bytes served | 13.2 KB across 11 responses |
| Screenshots | 7 captured |

## How a request flows

```text
client
  │  HTTP
  ▼
wsgi.py ──▶ ehco/app.py:get_app()
                │  reads config once (ehco/config.py)
                │  registers the `relay` blueprint
                ▼
           route handler
             ├──▶ ehco/models.py        tables, via Flask-SQLAlchemy
             ├──▶ ehco/errors.py        raises typed errors → one JSON envelope
             └──▶ ehco/observability.py JSON log line + X-Request-ID
```

Every response carries `X-Request-ID`, and the matching log line is written once at the end of the request with the status and duration, so a report of "it failed" is one `grep` away from the traceback.

## Architecture

```
relaylane/
├── src/ehco/
│   ├── http.py                         379  HTTP plumbing for ehco: correlation ids, access logs
│   ├── _app.py                         238  Web UI for ehco: tunnel/upstream management on top o
│   ├── observability.py                169  Structured logging and request correlation for ehco
│   ├── config.py                       168  Environment-driven configuration for ehco
│   ├── app.py                          119  Application factory for ehco
│   ├── errors.py                       108  Typed application errors and their HTTP mapping for 
│   ├── relay/tcp.py                     79  
│   ├── relay/api.py                     70  
│   ├── cli.py                           54  
│   ├── paths.py                         52  Filesystem layout for ehco
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
| Coverage | `pytest --cov` | floor in `pyproject.toml`, set below the measured value |
| Lint | `ruff check src tests` | zero findings |
| Format | `ruff format --check src tests` | zero reformats |
| Types | `mypy src` | zero errors |
| Security | `bandit -c pyproject.toml -r src` | reviewed skip list, no unreviewed finding |
| Live routes | boot `wsgi.py`, one GET per documented path | no 5xx, no undocumented guard |

CI runs the first six on Python 3.11, 3.12 and 3.13 on every push to `main`, plus a container build — [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Development

```sh
pip install -e ".[dev]"
python -m pytest -q                      # the suite
python -m pytest --cov                   # with the coverage floor
python -m ruff check src tests           # lint
python -m ruff format --check src tests  # formatting
python -m mypy src                       # types
python -m bandit -c pyproject.toml -r src  # security
pre-commit install                       # the same checks on commit
```

Dependabot opens grouped PRs for the dev tooling weekly and for actions and the base image monthly.

## Deploy

```sh
docker build -t relaylane .
docker run --rm -p 8000:8000 --env-file .env.example relaylane
```

A `docker-compose.yml` is included for a local run with a volume for the SQLite file. The image runs as a non-root user and serves through gunicorn.

## Limits, stated rather than hidden

- Upstream health is a passive flag, not an active probe.
- TLS termination is pass-through; certificate files are referenced but not reloaded on change.

## License

MIT — see [LICENSE](LICENSE).
