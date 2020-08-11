#!/usr/bin/env python
# -*- coding: utf-8 -*-
import unittest

from youtube_dl.utils import DownloadError

from catt.controllers import Cache
from catt.controllers import CCInfo
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
            "https://www.youtube.com/playlist?list=PL9Z0stL3aRykWNoVQW96JFIkelka_93Sc", throw_ytdl_dl_errs=True
        )
        self.assertIsNone(stream.video_url)
        self.assertEqual(stream.playlist_id, "PL9Z0stL3aRykWNoVQW96JFIkelka_93Sc")
        self.assertTrue(stream.is_playlist)
        self.assertEqual(stream.extractor, "youtube")

    def test_stream_info_other_video(self):
        stream = StreamInfo("https://www.twitch.tv/buddha/clip/OutstandingSquareMallardBudStar")
        self.assertIn("https://", stream.video_url)
        self.assertEqual(stream.video_id, "471296669")
        self.assertTrue(stream.is_remote_file)
        self.assertEqual(stream.extractor, "twitch")

    def test_cache(self):
        cache = Cache()
        cache.set_data("name", CCInfo("192.168.0.6", 8009, "Fake Factory Inc.", "Fakecast", "fake"))
        self.assertEqual(
            cache.get_data("name").all_info,
            {
                "ip": "192.168.0.6",
                "port": 8009,
                "manufacturer": "Fake Factory Inc.",
                "model_name": "Fakecast",
                "cast_type": "fake",
            },
        )

        cache.clear()
        cache = Cache()
        self.assertEqual(cache.get_data("name"), None)
        cache.clear()


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
