import os
import sys
import unittest

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

from hca.util.pool import ThreadPool


class TestThreadPool(unittest.TestCase):

    def setUp(self):
        self.pool = ThreadPool()
        self.count = 0

    def test_add_task(self):
        self.pool.add_task(self._add_to_count, 5)
        self.pool.add_task(self._add_to_count, 10)
        self.pool.add_task(self._add_to_count, 15)
        self.pool.wait_for_completion()
        self.assertEqual(self.count, 30)

    def _add_to_count(self, amount):
        self.count += amount
