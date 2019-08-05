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
    import mock
    import unittest2 as unittest

    TemporaryDirectory = backports.tempfile.TemporaryDirectory
else:
    import unittest
    from unittest import mock

    TemporaryDirectory = tempfile.TemporaryDirectory


class TestDssApi(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = hca.auth.AuthClient(swagger_url="https://auth.dev.data.humancellatlas.org/swagger.json")

    def test_login(self):
        resp = self.client.login()

    def test_get_users(self):
        user_id = 'trent.smith@chanzuckerberg.com'
        resp = self.client.get_v1_users()
        resp = self.client.get_v1_user(user_id=user_id)
        resp = self.client.get_v1_user_groups(user_id=user_id)
        resp = self.client.get_v1_user_roles(user_id=user_id)
        resp = self.client.get_v1_user_owns(user_id=user_id, )
        pass





if __name__ == "__main__":
    unittest.main()
