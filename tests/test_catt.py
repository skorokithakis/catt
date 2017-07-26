#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import unittest

from catt.controllers import Cache
from catt.stream_info import StreamInfo


class TestThings(unittest.TestCase):
    def test_stream_info_youtube_video(self):
        stream = StreamInfo("https://www.youtube.com/watch?v=VZMfhtKa-wo")
        self.assertIn("https://", stream.video_url)
        self.assertEqual(stream.video_id, "VZMfhtKa-wo")
        self.assertTrue(stream.is_youtube_video)

    def test_stream_info_youtube_playlist(self):
        stream = StreamInfo("https://www.youtube.com/playlist?list=PL9Z0stL3aRykWNoVQW96JFIkelka_93Sc")
        self.assertIsNone(stream.video_url)
        self.assertEqual(stream.playlist_id, "PL9Z0stL3aRykWNoVQW96JFIkelka_93Sc")
        self.assertTrue(stream.is_youtube_playlist)

    def test_stream_info_other_video(self):
        stream = StreamInfo("http://www.bbc.com/travel/story/20170719-a-new-life-for-bermudas-shipwrecks")
        self.assertIn("https://", stream.video_url)
        self.assertFalse(stream.is_youtube_video)
        self.assertFalse(stream.is_youtube_playlist)

    def test_cache(self):
        cache = Cache()
        cache.set("key", "value")
        self.assertEqual(cache.get("key"), "value")

        time.sleep(1.2)
        cache = Cache(duration=1)
        self.assertEqual(cache.get("key"), None)

        cache.set("key", "value")
        cache.clear()
        cache = Cache()
        self.assertEqual(cache.get("key"), None)
        cache.clear()


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
