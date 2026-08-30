---
id: rep-qgnlj
status: closed
deps: []
links: []
created: 2026-08-30T10:29:45Z
type: bug
priority: 2
assignee: Stavros Korokithakis
external-ref: gh-493
---
# Add regression test for catt scan -j JSON output

Objective: guard the `catt scan -j` JSON path against pychromecast attribute drift.

Background: in 0.13.1, `scan -j` called `d._asdict()` on the objects from `get_cast_infos()`. `pychromecast.CastInfo` is a frozen dataclass in 14.x, not a NamedTuple, so that raised AttributeError (GitHub issue 493). Commit cb90c11 already fixed the production code (catt/cli.py:592-605 now reads the six fields by name). This ticket only adds the missing test.

Scope: tests/test_catt.py only. No production code changes.

Requirements:
- Use click.testing.CliRunner to invoke the `scan` command with `-j`.
- Patch `catt.cli.get_cast_infos` to return a list containing a REAL `pychromecast.CastInfo` instance. Do NOT use a Mock for the CastInfo: a Mock auto-creates any attribute, so the test would still pass if the fields were renamed or removed. Using the real dataclass is the entire point of the test.
- Assert exit code 0, and that the parsed JSON is keyed by friendly_name and contains host, port, uuid, model_name, friendly_name, manufacturer.
- The uuid field is a uuid.UUID; echo_json serialises it via `default=str`. Assert the string form.
- Follow the existing style in tests/test_catt.py (unittest.TestCase classes, mock.patch context managers).

Non-goals:
- Do not change the scan JSON output shape (cast_type and services are intentionally absent).
- Do not touch the pychromecast pin.
- Do not add a test for plain `catt scan` (non-JSON).

Ready for implementation.

