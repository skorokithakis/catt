# AGENTS.md

Guide for AI agents (and new human contributors) working in this repo.

## What this project is

**catt** (Cast All The Things) is a CLI + small Python API for sending media
from many online sources to a Chromecast. The CLI entry point is
`catt.cli:main`; the public Python API lives in `catt/api.py`.

## Stack

- **Language:** Python `>= 3.11` (classifiers cover 3.11 / 3.12 / 3.13).
- **Package manager / build:** Poetry (`pyproject.toml` is the single source
  of truth for dependencies and version). `setup.cfg` and `tox.ini` are
  legacy and stale — do not rely on them.
- **Key runtime deps:** `click`, `pychromecast`, `yt-dlp`, `requests`,
  `ifaddr`.
- **Lint / format / type-check:** `ruff` (lint + format) and `mypy`, both
  driven by `pre-commit`.
- **Tests:** `pytest`.

## Commands

```bash
# Install dev environment
poetry install

# Lint, format, type-check (everything wired in .pre-commit-config.yaml)
pre-commit run --all-files

# Unit tests
pytest tests/
```

`tox.ini` targets py36–py39 and invokes `python setup.py test` — it is
stale, ignore it.

## Repo layout

| Path | Purpose |
|---|---|
| `catt/cli.py` | Click-based CLI; user-facing entry point. |
| `catt/controllers.py` | All Chromecast device + media control logic. Every `pychromecast` device/media call goes through here. |
| `catt/discovery.py` | mDNS / network discovery. All `pychromecast.discovery.*` calls live here. |
| `catt/api.py` | Public Python API (`CattDevice`); thin wrapper over controllers + discovery. |
| `catt/stream_info.py` | yt-dlp integration; URL resolution and stream metadata. |
| `catt/http_server.py` | Local HTTP server for casting local files. |
| `catt/subs_info.py` | Subtitle handling. |
| `catt/error.py` | Custom exception hierarchy used throughout. |
| `tests/` | Unit tests (pytest). |
| `realcc_tests/` | Manual / integration tests that require a real Chromecast. |
| `examples/` | Standalone usage examples. |
| `catt_receiver/` | Custom receiver app assets. |

## Conventions

- **Narrow custom exceptions** per domain (`CastError`, `AppSelectionError`,
  `ControllerError`, `ListenerError`, `StateFileError`, `APIError` in
  `catt/error.py`). Don't introduce broad `except Exception`.
- **No asyncio.** Concurrency is `threading.Event`-based; blocking calls
  paired with event waits (`CastStatusListener`, `MediaStatusListener`,
  `SimpleListener` in `controllers.py`).
- **Type annotations** on public functions and class fields.
- **Import pychromecast sub-modules narrowly** (e.g.
  `from pychromecast.controllers.dashcast import DashCastController`)
  rather than star-importing the top level.

## pychromecast pin policy

Current pin (in `pyproject.toml`):

```
pychromecast = ">=14.0.1, <15"
```

The upper bound is intentional. pychromecast has shipped breaking API
changes across majors (discovery API, `socket_client` restructuring, etc.).
When a new major ships, treat the bump as a small project of its own:
audit `catt/discovery.py`, `catt/controllers.py`, and `catt/api.py` against
the changelog before widening the cap.

Issue [#444](https://github.com/skorokithakis/catt/issues/444) asked for
`pychromecast > 14`. That ask was already satisfied by the current pin
(any 14.x is accepted, currently up to 14.0.10). No 15.x exists on PyPI
yet; when it does, do the audit above rather than dropping the cap blindly.

## Known gotchas

- **`catt/api.py:185` uses `c.socket_client.host`.** The `socket_client`
  attribute path was restructured in newer pychromecast versions; this
  call may be broken against current 14.x. The modern equivalent is
  `c.cast_info.host`. Verify against a real device before changing — and
  if you fix it, check whether anything else in `discovery.py` /
  `api.py` reads `socket_client` similarly.
- **`setup.cfg`** declares `python_requires >= 3.4`. Stale; the real floor
  is 3.11 (per `pyproject.toml`). Harmless but misleading.
- **`tox.ini`** is stale (see "Commands" above).

## When making changes

1. Edit `pyproject.toml` for dependency changes; do not touch
   `requirements_dev.txt` or `setup.cfg` for runtime deps.
2. Run `pre-commit run --all-files` before committing.
3. Add or update tests in `tests/` for behaviour changes. `realcc_tests/`
   is for changes that genuinely need a live Chromecast — most PRs should
   not require it.
4. The version is managed by release-please
   (`.release-please-manifest.json`, `release-please-config.json`); do not
   hand-bump `pyproject.toml`'s `version` field in normal PRs.
