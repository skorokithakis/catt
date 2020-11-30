#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from youtube_dl.utils import DownloadError

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
        stream = StreamInfo("https://www.youtube.com/watch?v=VZMfhtKa-wo", throw_ytdl_dl_errs=True)
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
        stream = StreamInfo("https://www.twitch.tv/twitch/clip/MistySoftPenguinKappaPride")
        self.assertIn("https://", stream.video_url)
        self.assertEqual(stream.video_id, "944456168")
        self.assertTrue(stream.is_remote_file)
        self.assertEqual(stream.extractor, "twitch")


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
