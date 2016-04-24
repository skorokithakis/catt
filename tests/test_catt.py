#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import unittest

from catt import catt


class TestThings(unittest.TestCase):
    def test_get_stream_url(self):
        url = catt.get_stream_url("https://www.youtube.com/watch?v=VZMfhtKa-wo")
        self.assertIn("https://", url)

    def test_cache(self):
        cache = catt.Cache("/tmp/catt_cache/")
        cache.set("key", "value")
        self.assertEquals(cache.get("key", 1), "value")
        time.sleep(1.2)
        self.assertIsNone(cache.get("key", 1))


if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())
