#!/usr/bin/env python
# coding: utf-8
import os
import sys
import tempfile

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.auth
from hca.util.compat import USING_PYTHON2

if USING_PYTHON2:
    import backports.tempfile
    import unittest2 as unittest

    TemporaryDirectory = backports.tempfile.TemporaryDirectory
else:
    import unittest

    TemporaryDirectory = tempfile.TemporaryDirectory


class TestDssApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = hca.auth.AuthClient(swagger_url="https://auth.dev.data.humancellatlas.org/swagger.json")

    def test_smoke(self):
        self.client.get_well_known_openid_configuration()
if __name__ == "__main__":
    unittest.main()
