#!/usr/bin/env python
# -*- coding: utf-8 -*-
import concurrent.futures
import contextlib
import json
import time
import unittest
import uuid
from unittest import mock

import click
import click.testing
from pychromecast import CastInfo
from pychromecast.error import RequestTimeout
from yt_dlp.utils import DownloadError

from catt.cli import YTDL_OPT
from catt.cli import scan
from catt.controllers import App
from catt.controllers import CastController
from catt.controllers import DASHCAST_APP_ID
from catt.controllers import DashCastController
from catt.controllers import DefaultCastController
from catt.controllers import MEDIA_RECEIVER_APP_ID
from catt.controllers import MediaStatusListener
from catt.controllers import PlaybackBaseMixin
from catt.controllers import SimpleListener
from catt.controllers import YOUTUBE_APP_ID
from catt.controllers import YoutubeCastController
from catt.discovery import get_cast_with_ip
from catt.discovery import get_casts
from catt.error import CastError
from catt.stream_info import StreamInfo
from catt.util import guess_mime


def ignore_tmr_failure(func):
    """
    Ignore "Too many requests" failures in a test.

    YouTube will sometimes throttle us and cause the tests to flap. This decorator
    catches the "Too many requests" exceptions in tests and ignores them.
    """

    def wrapper(*args):
        try:
            return func(*args)
        except DownloadError as err:
            if "HTTP Error 429:" in str(err):
                pass
            else:
                raise

    return wrapper


class TestThings(unittest.TestCase):
    @ignore_tmr_failure
    def test_stream_info_youtube_video(self):
        stream = StreamInfo(
            "https://www.youtube.com/watch?v=VZMfhtKa-wo", throw_ytdl_dl_errs=True
        )
        self.assertIn("https://", stream.video_url)
        self.assertEqual(stream.video_id, "VZMfhtKa-wo")
        self.assertTrue(stream.is_remote_file)
        self.assertEqual(stream.extractor, "youtube")

    @ignore_tmr_failure
    def test_stream_info_youtube_playlist(self):
        stream = StreamInfo(
            "https://www.youtube.com/playlist?list=PL9Z0stL3aRykWNoVQW96JFIkelka_93Sc",
            throw_ytdl_dl_errs=True,
        )
        self.assertIsNone(stream.video_url)
        self.assertEqual(stream.playlist_id, "PL9Z0stL3aRykWNoVQW96JFIkelka_93Sc")
        self.assertTrue(stream.is_playlist)
        self.assertEqual(stream.extractor, "youtube")

    def test_stream_info_other_video(self):
        stream = StreamInfo(
            "https://www.twitch.tv/twitch/clip/MistySoftPenguinKappaPride"
        )
        self.assertIn("https://", stream.video_url)
        self.assertEqual(stream.video_id, "492743767")
        self.assertTrue(stream.is_remote_file)
        self.assertEqual(stream.extractor, "twitch")

    def test_stream_info_direct_link(self):
        url = "https://upload.wikimedia.org/wikipedia/commons/c/c8/Example.ogg"
        stream = StreamInfo(url)
        self.assertEqual(stream.video_url, url)
        self.assertTrue(stream.is_remote_file)
        self.assertTrue(stream._is_direct_link)


class TestGuessMime(unittest.TestCase):
    def test_opus_returns_audio_ogg(self):
        self.assertEqual(guess_mime("song.opus"), "audio/ogg")
        self.assertEqual(guess_mime("song.OPUS"), "audio/ogg")

    def test_ogg_returns_audio_ogg(self):
        self.assertEqual(guess_mime("song.ogg"), "audio/ogg")

    def test_oga_returns_audio_ogg(self):
        self.assertEqual(guess_mime("song.oga"), "audio/ogg")

    def test_flac_returns_audio_flac(self):
        self.assertEqual(guess_mime("song.flac"), "audio/flac")

    def test_wav_returns_audio_wav(self):
        self.assertEqual(guess_mime("song.wav"), "audio/wav")

    def test_aac_returns_audio_aac(self):
        self.assertEqual(guess_mime("song.aac"), "audio/aac")

    def test_unknown_extension_falls_back_to_video_mp4(self):
        self.assertEqual(guess_mime("song.xyz"), "video/mp4")

    def test_existing_mp4_still_works(self):
        self.assertEqual(guess_mime("movie.mp4"), "video/mp4")


class TestYtdlOpt(unittest.TestCase):
    def _convert(self, value):
        """Helper to call YTDL_OPT.convert with minimal context."""
        ctx = click.Context(click.Command("test"))
        return YTDL_OPT.convert(value, param=None, ctx=ctx)

    def test_list_basic(self):
        """-y key=[a,b] parses to ('key', ['a', 'b'])."""
        key, val = self._convert("allowed_extractors=[youtube,generic]")
        self.assertEqual(key, "allowed_extractors")
        self.assertEqual(val, ["youtube", "generic"])

    def test_list_with_whitespace(self):
        """-y key=[ a , b ] parses to ('key', ['a', 'b'])."""
        key, val = self._convert("key=[ a , b ]")
        self.assertEqual(key, "key")
        self.assertEqual(val, ["a", "b"])

    def test_list_empty(self):
        """-y key=[] parses to ('key', [])."""
        key, val = self._convert("key=[]")
        self.assertEqual(key, "key")
        self.assertEqual(val, [])

    def test_list_empty_with_space(self):
        """-y key=[ ] parses to ('key', [])."""
        key, val = self._convert("key=[ ]")
        self.assertEqual(key, "key")
        self.assertEqual(val, [])

    def test_bool_true(self):
        """-y key=true still parses to ('key', True)."""
        key, val = self._convert("key=true")
        self.assertEqual(key, "key")
        self.assertEqual(val, True)

    def test_bool_false(self):
        """-y key=false still parses to ('key', False)."""
        key, val = self._convert("key=false")
        self.assertEqual(key, "key")
        self.assertEqual(val, False)

    def test_plain_string(self):
        """-y key=plain still parses to ('key', 'plain')."""
        key, val = self._convert("key=plain")
        self.assertEqual(key, "key")
        self.assertEqual(val, "plain")


class TestScan(unittest.TestCase):
    def test_scan_json_outputs_cast_info_fields(self):
        cast_info = CastInfo(
            services=set(),
            uuid=uuid.UUID("12345678-1234-5678-1234-567812345678"),
            model_name="Chromecast",
            friendly_name="Living Room",
            host="192.168.1.10",
            port=8009,
            cast_type="cast",
            manufacturer="Google Inc.",
        )

        runner = click.testing.CliRunner()
        with mock.patch("catt.cli.get_cast_infos", return_value=[cast_info]):
            result = runner.invoke(scan, ["-j"])

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(
            json.loads(result.output),
            {
                "Living Room": {
                    "host": "192.168.1.10",
                    "port": 8009,
                    "uuid": "12345678-1234-5678-1234-567812345678",
                    "model_name": "Chromecast",
                    "friendly_name": "Living Room",
                    "manufacturer": "Google Inc.",
                }
            },
        )


class _FakeStatus:
    """Minimal stub for pychromecast media status."""

    player_state = "UNKNOWN"


class _FakeMediaController:
    """Minimal stub for pychromecast MediaController."""

    def __init__(self):
        self.status = _FakeStatus()
        self._listener = None

    def register_status_listener(self, listener):
        self._listener = listener


class _FakeCast:
    """Minimal stub for pychromecast.Chromecast."""

    def __init__(self):
        self.media_controller = _FakeMediaController()


class _WaitForStub(PlaybackBaseMixin):
    """Minimal stub exposing PlaybackBaseMixin.wait_for for testing."""

    def __init__(self):
        self._cast = _FakeCast()


class TestLoadMediaFailed(unittest.TestCase):
    def test_media_status_listener_records_error_and_unblocks(self):
        """load_media_failed records error code and unblocks wait_for_states."""
        listener = MediaStatusListener(current_state="UNKNOWN", states=["PLAYING"])
        self.assertIsNone(listener.load_failed_error_code)
        listener.load_media_failed(0, 42)
        self.assertTrue(listener.wait_for_states(timeout=1))
        self.assertEqual(listener.load_failed_error_code, 42)

    def test_simple_listener_unblocks_on_load_failed(self):
        """load_media_failed unblocks block_until_status_received."""
        listener = SimpleListener()
        listener.load_media_failed(0, 42)
        # Returns immediately because the internal event is already set.
        listener.block_until_status_received()

    def test_wait_for_raises_casterror_on_load_failure(self):
        """PlaybackBaseMixin.wait_for raises CastError with the error code."""
        stub = _WaitForStub()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(stub.wait_for, ["PLAYING"], False, 2)

            # Wait until the listener has been registered.
            mc = stub._cast.media_controller
            while mc._listener is None:
                time.sleep(0.01)

            # Trigger a load failure.
            mc._listener.load_media_failed(0, 7)

            with self.assertRaises(CastError) as ctx:
                future.result()
            self.assertIn("error code 7", str(ctx.exception))


class TestDiscoveryTimeout(unittest.TestCase):
    @contextlib.contextmanager
    def _patch_discovery(self, fake_cast):
        """Patch discovery and cast construction, returning the context managers."""
        browser = mock.Mock()
        with (
            mock.patch(
                "catt.discovery.pychromecast.discovery.discover_chromecasts",
                return_value=([object()], browser),
            ),
            mock.patch(
                "catt.discovery.pychromecast.get_chromecast_from_cast_info",
                return_value=fake_cast,
            ),
        ):
            yield browser

    def test_get_casts_raises_casterror_when_device_does_not_connect(self):
        fake_cast = mock.Mock()
        fake_cast.cast_info.friendly_name = "Kitchen"
        fake_cast.wait.side_effect = RequestTimeout("wait", 30)

        with self._patch_discovery(fake_cast) as browser:
            with self.assertRaises(CastError) as ctx:
                get_casts()

        fake_cast.wait.assert_called_once_with(timeout=30)
        browser.stop_discovery.assert_called_once_with()
        self.assertIn("Kitchen", str(ctx.exception))
        self.assertIn("did not respond", str(ctx.exception))

    def test_get_casts_raises_casterror_when_wait_returns_without_connecting(self):
        # Some pychromecast versions return silently from wait() on expiry;
        # the connection state check must catch that case.
        fake_cast = mock.Mock()
        fake_cast.cast_info.friendly_name = "Kitchen"
        fake_cast.wait.return_value = None
        fake_cast.socket_client.is_connected = False

        with self._patch_discovery(fake_cast) as browser:
            with self.assertRaises(CastError) as ctx:
                get_casts()

        fake_cast.wait.assert_called_once_with(timeout=30)
        browser.stop_discovery.assert_called_once_with()
        self.assertIn("Kitchen", str(ctx.exception))

    def test_get_cast_with_ip_raises_casterror_when_device_does_not_connect(self):
        fake_cast = mock.Mock()
        fake_cast.wait.side_effect = RequestTimeout("wait", 30)
        device_info = mock.Mock()
        device_info.uuid = "deadbeef"
        device_info.model_name = "Chromecast"
        device_info.friendly_name = "Living Room"

        with (
            mock.patch(
                "catt.discovery.pychromecast.discovery.get_device_info",
                return_value=device_info,
            ),
            mock.patch(
                "catt.discovery.pychromecast.get_chromecast_from_host",
                return_value=fake_cast,
            ),
        ):
            with self.assertRaises(CastError) as ctx:
                get_cast_with_ip("192.168.1.10")

        fake_cast.wait.assert_called_once_with(timeout=30)
        self.assertIn("Living Room", str(ctx.exception))
        self.assertIn("192.168.1.10", str(ctx.exception))


class TestControllerTimeouts(unittest.TestCase):
    @contextlib.contextmanager
    def _fast_wait_timeout(self):
        """Temporarily shorten WAIT_TIMEOUT so timeout tests don't block for 30s."""
        with mock.patch("catt.controllers.WAIT_TIMEOUT", 0.01):
            yield

    def _make_cast(self, app_id):
        cast = mock.Mock()
        cast.app_id = app_id
        return cast

    def _make_app(self, name, app_id, device_types):
        return App(app_name=name, app_id=app_id, supported_device_types=device_types)

    def test_dashcast_prep_app_raises_casterror_when_app_never_becomes_ready(self):
        cast = self._make_cast(None)
        app = self._make_app("dashcast", DASHCAST_APP_ID, ["cast", "audio"])
        controller = DashCastController(cast, app, prep=None)

        with self._fast_wait_timeout():
            with self.assertRaises(CastError) as ctx:
                controller.prep_app()

        cast.start_app.assert_called_once_with(DASHCAST_APP_ID, force_launch=True)
        self.assertIn("timed out", str(ctx.exception))
        self.assertIn(DASHCAST_APP_ID, str(ctx.exception))

    def test_prep_app_raises_casterror_when_app_never_becomes_ready(self):
        cast = self._make_cast("12345678")
        app = self._make_app("default", MEDIA_RECEIVER_APP_ID, ["cast", "audio"])
        controller = CastController(cast, app, prep=None)

        with self._fast_wait_timeout():
            with self.assertRaises(CastError) as ctx:
                controller.prep_app()

        cast.start_app.assert_called_once_with(MEDIA_RECEIVER_APP_ID)
        self.assertIn("timed out", str(ctx.exception))
        self.assertIn(MEDIA_RECEIVER_APP_ID, str(ctx.exception))

    def test_kill_force_quits_app_even_when_cloud_app_never_becomes_ready(self):
        cast = self._make_cast("12345678")
        app = self._make_app("default", MEDIA_RECEIVER_APP_ID, ["cast", "audio"])
        controller = CastController(cast, app, prep=None)

        with self._fast_wait_timeout():
            controller.kill(force=True)

        cast.quit_app.assert_called_once_with()

    def test_block_until_status_received_raises_casterror_when_status_never_arrives(
        self,
    ):
        listener = SimpleListener()

        with self._fast_wait_timeout():
            with self.assertRaises(CastError) as ctx:
                listener.block_until_status_received()

        self.assertIn("media status", str(ctx.exception))
        self.assertIn("timed out", str(ctx.exception))

    def test_play_media_url_raises_casterror_when_media_session_never_becomes_active(
        self,
    ):
        cast = self._make_cast(MEDIA_RECEIVER_APP_ID)
        app = self._make_app("default", MEDIA_RECEIVER_APP_ID, ["cast", "audio"])
        controller = DefaultCastController(cast, app, prep=None)
        controller._controller.session_active_event.is_set.return_value = False

        with mock.patch("catt.controllers.WAIT_TIMEOUT", mock.sentinel.timeout):
            with self.assertRaises(CastError) as ctx:
                controller.play_media_url("https://example.com/video.mp4")

        controller._controller.block_until_active.assert_called_once_with(
            timeout=mock.sentinel.timeout
        )
        self.assertIn("media session", str(ctx.exception))
        self.assertIn("timed out", str(ctx.exception))

    def test_youtube_play_media_id_raises_casterror_when_playback_never_starts(self):
        cast = self._make_cast(YOUTUBE_APP_ID)
        app = self._make_app("youtube", YOUTUBE_APP_ID, ["cast"])
        with mock.patch("catt.controllers.YouTubeController"):
            controller = YoutubeCastController(cast, app, prep=None)

        with mock.patch("catt.controllers.WAIT_TIMEOUT", mock.sentinel.timeout):
            with mock.patch.object(
                controller, "wait_for", return_value=False
            ) as wait_for:
                with self.assertRaises(CastError) as ctx:
                    controller.play_media_id("abc123", current_time=42)

        wait_for.assert_called_once_with(["PLAYING"], timeout=mock.sentinel.timeout)
        self.assertIn("PLAYING", str(ctx.exception))
        self.assertIn("seconds", str(ctx.exception))

    def test_youtube_add_raises_casterror_when_still_buffering(self):
        cast = self._make_cast(YOUTUBE_APP_ID)
        app = self._make_app("youtube", YOUTUBE_APP_ID, ["cast"])
        with mock.patch("catt.controllers.YouTubeController"):
            controller = YoutubeCastController(cast, app, prep=None)

        with mock.patch("catt.controllers.WAIT_TIMEOUT", mock.sentinel.timeout):
            with mock.patch.object(
                controller, "wait_for", return_value=False
            ) as wait_for:
                with self.assertRaises(CastError) as ctx:
                    controller.add("abc123")

        wait_for.assert_called_once_with(
            ["BUFFERING"], invert=True, timeout=mock.sentinel.timeout
        )
        self.assertIn("buffering", str(ctx.exception))
        self.assertIn("seconds", str(ctx.exception))


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())  # type: ignore
