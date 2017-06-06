#!/usr/bin/env python
# coding: utf-8

from __future__ import absolute_import, division, print_function, unicode_literals

import os, sys, unittest, tempfile, json, subprocess

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, pkg_root)

import hca

class TestHCACLI(unittest.TestCase):
    def test_hca_cli(self):
        hca.main()

if __name__ == '__main__':
    unittest.main()
