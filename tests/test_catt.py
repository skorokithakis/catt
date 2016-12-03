#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import unittest

from catt.controllers import Cache, get_stream_info


class TestThings(unittest.TestCase):
    def test_get_stream_info(self):
        url = get_stream_info("https://www.youtube.com/watch?v=VZMfhtKa-wo")["url"]
        self.assertIn("https://", url)

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
