---
id: rep-phcbt
status: closed
deps: []
links: []
created: 2026-08-30T10:29:52Z
type: chore
priority: 2
assignee: Stavros Korokithakis
---
# Remove stale socket_client gotcha from AGENTS.md

Objective: AGENTS.md's 'Known gotchas' section claims `catt/api.py:185` uses `c.socket_client.host` and may be broken against current pychromecast 14.x. That is no longer true and now misdirects readers.

Current reality (verified):
- catt/api.py:188 uses `c.cast_info.host`.
- catt/api.py:54 uses `self._cast.cast_info.host`.
- The only remaining socket_client use is catt/discovery.py:33 (`cast.socket_client.is_connected`), which is still valid in pychromecast 14.x (Chromecast.socket_client exists).

Change: delete the `catt/api.py:185` / socket_client bullet from the 'Known gotchas' section of AGENTS.md.

Non-goals:
- Do not restructure or rewrite the rest of AGENTS.md.
- Do not remove the setup.cfg or tox.ini gotchas; those are still accurate.
- Do not touch any Python file.

Ready for implementation.

