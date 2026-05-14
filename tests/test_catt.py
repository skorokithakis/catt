#!/usr/bin/env python
# -*- coding: utf-8 -*-
import concurrent.futures
import time
import unittest

import click
import click.testing
from yt_dlp.utils import DownloadError

from catt.cli import YTDL_OPT
from catt.controllers import MediaStatusListener
from catt.controllers import PlaybackBaseMixin
from catt.controllers import SimpleListener
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
        url = "https://homeazan.com/file_example_MP3_700KB.mp3"
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


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())  # type: ignore
