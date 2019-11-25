#!/usr/bin/env python
# -*- coding: utf-8 -*-
import errno
import os
import sys
import unittest
from unittest.mock import patch

from hca.dss.util import hardlink

from test.unit import TmpDirTestCase

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.util


class TestUtils(unittest.TestCase):
    def test_dict_merge(self):
        dict1 = {'a': {'b': {'c': 1}}, 'd': 2}
        dict2 = {'a': {'b': {'d': 1}}, 'c': 2}
        dict3 = {'a': {'b': {'c': 1, 'd': 1}}, 'c': 2, 'd': 2}
        self.assertEqual(hca.util._merge_dict(dict1, dict2), dict3)


class TestLinking(TmpDirTestCase):
    """TmpDirTestCase will ensure any links / files we create are cleaned up"""
    src = 'link_source'
    dst = 'link_destination'

    def test_link_limit(self):
        """Ensure that we copy in the case that the link limit is reached"""
        os_error = OSError()
        os_error.errno = errno.EMLINK
        self._link_with_error(self.src, self.dst, os_error)
        source_stat = os.stat(self.src)
        dest_stat = os.stat(self.dst)
        self.assertTrue(source_stat.st_dev != dest_stat.st_dev or source_stat.st_ino != dest_stat.st_ino)

    def test_link_fails(self):
        """Ensure that linking fails in other cases"""
        for error in (ValueError(), RuntimeError()):
            with self.subTest(error=error):
                with self.assertRaises(type(error)):
                    self._link_with_error(self.src, self.dst, error)

    def _link_with_error(self, src, dst, error):
        with open(src, 'w'):
            pass
        with patch('os.link', side_effect=error):
            hardlink(src, dst)


if __name__ == "__main__":
    unittest.main()
