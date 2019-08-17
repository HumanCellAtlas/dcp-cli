#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import unittest

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.util


class TestUtils(unittest.TestCase):
    def test_dict_merge(self):
        dict1 = {'a': {'b': {'c': 1}}, 'd': 2}
        dict2 = {'a': {'b': {'d': 1}}, 'c': 2}
        dict3 = {'a': {'b': {'c': 1, 'd': 1}}, 'c': 2, 'd': 2}
        self.assertEqual(hca.util._merge_dict(dict1, dict2), dict3)

if __name__ == "__main__":
    unittest.main()
