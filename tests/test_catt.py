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
        stream = StreamInfo("http://www.dailymotion.com/video/x6fotne")
        self.assertIn("https://", stream.video_url)
        self.assertEqual(stream.video_id, "x6fotne")
        self.assertTrue(stream.is_remote_file)
        self.assertEqual(stream.extractor, "dailymotion")

    def test_cache(self):
        cache = Cache()
        cache.set_data("key", "value")
        self.assertEqual(cache.get_data("key"), "value")

        cache.clear()
        cache = Cache()
        self.assertEqual(cache.get_data("key"), None)
        cache.clear()


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
