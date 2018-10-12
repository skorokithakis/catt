#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from catt.controllers import Cache
from catt.stream_info import StreamInfo


class TestThings(unittest.TestCase):
    def test_stream_info_youtube_video(self):
        stream = StreamInfo("https://www.youtube.com/watch?v=VZMfhtKa-wo")
        self.assertIn("https://", stream.video_url)
        self.assertEqual(stream.video_id, "VZMfhtKa-wo")
        self.assertTrue(stream.is_remote_file)
        self.assertEqual(stream.extractor, "youtube")

    def test_stream_info_youtube_playlist(self):
        stream = StreamInfo("https://www.youtube.com/playlist?list=PL9Z0stL3aRykWNoVQW96JFIkelka_93Sc")
        self.assertIsNone(stream.video_url)
        self.assertEqual(stream.playlist_id, "PL9Z0stL3aRykWNoVQW96JFIkelka_93Sc")
        self.assertTrue(stream.is_playlist)
        self.assertEqual(stream.extractor, "youtube")

    def test_stream_info_other_video(self):
        stream = StreamInfo("https://clips.twitch.tv/CloudyEnticingChickpeaCeilingCat")
        self.assertIn("https://", stream.video_url)
        self.assertEqual(stream.video_id, "304482431")
        self.assertTrue(stream.is_remote_file)
        self.assertEqual(stream.extractor, "twitch")

    def test_cache(self):
        cache = Cache()
        cache.set_data("name", "ip", "port")
        self.assertEqual(cache.get_data("name"), ("ip", "port"))

        cache.clear()
        cache = Cache()
        self.assertEqual(cache.get_data("name"), (None, None))
        cache.clear()


if __name__ == "__main__":
    import sys

    sys.exit(unittest.main())
