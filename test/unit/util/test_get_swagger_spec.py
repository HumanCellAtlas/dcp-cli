#!/usr/bin/env python
# coding: utf-8

import os
import sys
import json
import unittest
import requests

pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))  # noqa
sys.path.insert(0, pkg_root)  # noqa

import hca.util
from hca import HCAConfig
from hca.util.compat import USING_PYTHON2
from test import TEST_DIR

if USING_PYTHON2:
    import mock
    from mock import mock_open
else:
    from unittest import mock
    from unittest.mock import mock_open


class TestSwaggerClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Initialize SwaggerClient with a test HCAConfig.
        """
        cls.swagger_url = "test_swagger_url"
        cls.open_fn_name = "__builtin__.open" if USING_PYTHON2 else "builtins.open"
        cls.test_response = requests.models.Response()
        cls.test_response.status_code = 200
        with open(os.path.join(TEST_DIR, "res", "test_swagger.json"), 'rb') as fh:
            cls.test_response._content = fh.read()

        with mock.patch('requests.Session.get') as mock_get, \
                mock.patch(cls.open_fn_name, mock_open()), \
                mock.patch('hca.util.fs.atomic_write'), \
                mock.patch('hca.dss.SwaggerClient.load_swagger_json') as mock_load_swagger_json:
            mock_get.return_value = cls.test_response
            mock_load_swagger_json.return_value = json.loads(cls.test_response._content.decode("utf-8"))

            config = HCAConfig(save_on_exit=False)
            config['SwaggerClient'] = {}
            config['SwaggerClient'].swagger_url = cls.swagger_url
            cls.client = hca.util.SwaggerClient(config)

    def setUp(self):
        self.client._swagger_spec = None
        self.client._spec_valid_for_days = 1
        self.client._session = requests.Session()

    def tearDown(self):
        self.client._swagger_spec = None

    def test_get_swagger_spec_new(self):
        with mock.patch('os.path.exists') as mock_exists, \
                mock.patch('hca.util.fs.get_days_since_last_modified') as mock_days_since_last_modified, \
                mock.patch('os.makedirs') as mock_makedirs, \
                mock.patch('requests.Session.get') as mock_get, \
                mock.patch('hca.dss.SwaggerClient.load_swagger_json'), \
                mock.patch('hca.util.fs.atomic_write') as mock_atomic_write, \
                mock.patch(self.open_fn_name, mock_open()):
            mock_exists.return_value = False
            mock_days_since_last_modified.return_value = 0
            mock_get.return_value = self.test_response
            self.client.config.pop('swagger_filename')

            test = self.client.swagger_spec
            self.assertTrue(mock_makedirs.called)
            mock_get.assert_called_with(self.swagger_url)
            mock_atomic_write.assert_called_with(mock.ANY,
                                                 self.test_response._content)

    def test_get_swagger_spec_cache_valid(self):
        with mock.patch('os.path.exists') as mock_exists, \
                mock.patch('hca.util.fs.get_days_since_last_modified') as mock_days_since_last_modified, \
                mock.patch('os.makedirs') as mock_makedirs, \
                mock.patch('requests.Session.get') as mock_get, \
                mock.patch('hca.dss.SwaggerClient.load_swagger_json'), \
                mock.patch('hca.util.fs.atomic_write') as mock_atomic_write, \
                mock.patch(self.open_fn_name, mock_open()):
            mock_exists.return_value = True
            mock_days_since_last_modified.return_value = 0
            mock_get.return_value = self.test_response

            test = self.client.swagger_spec
            self.assertFalse(mock_makedirs.called)
            self.assertFalse(mock_get.called)
            self.assertFalse(mock_atomic_write.called)

    def test_get_swagger_spec_cache_expired(self):
        with mock.patch('os.path.exists') as mock_exists, \
                mock.patch('hca.util.fs.get_days_since_last_modified') as mock_days_since_last_modified, \
                mock.patch('os.makedirs'), \
                mock.patch('requests.Session.get') as mock_get, \
                mock.patch('hca.dss.SwaggerClient.load_swagger_json'), \
                mock.patch('hca.util.fs.atomic_write') as mock_atomic_write, \
                mock.patch(self.open_fn_name, mock_open()):
            mock_exists.return_value = True
            mock_days_since_last_modified.return_value = 2
            mock_get.return_value = self.test_response

            test = self.client.swagger_spec
            mock_get.assert_called_with(mock.ANY)
            mock_atomic_write.assert_called_with(mock.ANY,
                                                 self.test_response._content)

    def test_get_swagger_spec_local_config(self):
        with mock.patch('os.makedirs') as mock_makedirs, \
                mock.patch('requests.Session.get') as mock_get, \
                mock.patch('hca.dss.SwaggerClient.load_swagger_json'), \
                mock.patch('hca.util.fs.atomic_write') as mock_atomic_write, \
                mock.patch(self.open_fn_name, mock_open()):
            self.client.config.swagger_filename = "filename"

            test = self.client.swagger_spec
            self.assertFalse(mock_makedirs.called)
            self.assertFalse(mock_get.called)
            self.assertFalse(mock_atomic_write.called)


if __name__ == "__main__":
    unittest.main()
