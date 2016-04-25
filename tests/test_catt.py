#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import unittest

from catt.controllers import Cache, get_stream_url


class TestThings(unittest.TestCase):
    def test_get_stream_url(self):
        url = get_stream_url("https://www.youtube.com/watch?v=VZMfhtKa-wo")
        self.assertIn("https://", url)

    def test_cache(self):
        cache = Cache()
        cache.set("key", "value")
        self.assertEqual(cache.get("key", 1), "value")
        time.sleep(1.2)
        self.assertIsNone(cache.get("key", 1))

        cache.set("key", "value")
        cache.clear()
        self.assertIsNone(cache.get("key", 100))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
