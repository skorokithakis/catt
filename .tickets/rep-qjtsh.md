---
id: rep-qjtsh
status: closed
deps: []
links: []
created: 2026-08-14T06:31:09Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Add connection timeout to cast.wait() in discovery

Objective: catt must not hang forever when a Chromecast device is unreachable or unresponsive (GitHub issue #492: a hung catt child process holds an inherited Domoticz socket, blocking port 9090 on Domoticz restart).

Scope: catt/discovery.py only — the two unbounded cast.wait() calls (get_casts line ~36, get_cast_with_ip line ~96). Pass a 30-second timeout. If the connection is not established when the wait expires, raise CastError with a message naming the device/IP and saying it did not respond.

Caveat: pychromecast's Chromecast.wait(timeout) waits on a threading.Event and may return silently on expiry — verify the semantics in the pinned pychromecast 14.x and check connection state after the wait (e.g. socket_client status) before deciding success. Define the timeout as a module-level constant.

Non-goals: do not touch the Event.wait() calls in controllers.py; no CLI flag for the timeout; no changes to http_server or stream_info.

## Acceptance Criteria

Unit test in tests/ covering the timeout path (mock a cast whose wait() expires without connecting) asserting CastError is raised. Existing tests and pre-commit run --all-files pass.


## Notes

**2026-08-14T06:38:31Z**

ready for implementation
