---
id: rep-xrozx
status: closed
deps: []
links: []
created: 2026-08-19T15:34:24Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Bound every unbounded wait in controllers.py

Objective: catt must never block forever waiting on a Chromecast. A hung catt process holds file descriptors it inherited from its parent (GitHub #492: an inherited Domoticz listen socket keeps the port bound after Domoticz restarts). The earlier fix (rep-qjtsh) only bounded the discovery waits; the cast_site / DashCast path still hangs.

Scope: catt/controllers.py plus tests/.

Add a module-level constant WAIT_TIMEOUT = 30 (seconds) and apply it to:

1. DashCastController.prep_app (~line 612) - self._cast_listener.app_ready.wait(). This is the reported bug. Raise CastError on expiry.
2. CastController.prep_app (~line 318) - same unbounded app_ready.wait(). Raise CastError on expiry.
3. SimpleListener.block_until_status_received (~line 285) - self._status_received.wait(), used by _update_status. Raise CastError on expiry.
4. CastController.kill(force=True) (~line 479) - listener.app_ready.wait(). DO NOT raise here. This wait is best-effort before quit_app(); time out and fall through to quit_app() regardless, or 'catt stop -f' breaks.
5. YoutubeCastController (~lines 627, 636, 640, 644) - four wait_for() calls that pass no timeout. Pass WAIT_TIMEOUT and raise CastError when wait_for returns False.

Error messages must name what catt was waiting for (app name/id, or 'status') and the timeout, in the style of discovery.py's _wait_for_cast.

Non-goals:
- Do NOT touch cli.py:354, cst.wait_for(['UNKNOWN','IDLE']). That unbounded wait is intentional: it blocks until playback ends.
- No CLI flag or config option for the timeout.
- No changes to discovery.py, api.py, http_server.py, or stream_info.py.
- Do not close inherited file descriptors. That was considered and rejected.

## Design

Reuse the shape of discovery.py's _wait_for_cast: a helper that waits with a timeout and raises CastError with a descriptive message. Keep the threading.Event style; no asyncio.

kill(force=True) is deliberately the odd one out. Its wait only exists to give the dummy Cloud app time to start before quitting the session. Failing to launch that app must not stop the kill from happening.

## Acceptance Criteria

Unit tests cover the DashCastController.prep_app timeout path (CastError raised) and assert that kill(force=True) still calls quit_app() after its wait expires. pytest and pre-commit run --all-files pass.


## Notes

**2026-08-19T15:34:31Z**

ready for implementation
