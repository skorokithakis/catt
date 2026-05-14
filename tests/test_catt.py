#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

import click
import click.testing
from yt_dlp.utils import DownloadError

from catt.cli import YTDL_OPT
from catt.stream_info import StreamInfo


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


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())  # type: ignore
