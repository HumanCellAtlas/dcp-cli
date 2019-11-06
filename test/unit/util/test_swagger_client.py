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
from test import TEST_DIR
from unittest import mock
from unittest.mock import mock_open


import time
from hca.dss import DSSClient


class TestTokenDSSClient(DSSClient):
    """Mocked client that always expires request tokens within 1 second."""
    token_expiration = 1

    def __init__(self, *args, **kwargs):
        super(TestTokenDSSClient, self).__init__(*args, **kwargs)


class TestSwaggerClient(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """
        Initialize SwaggerClient with a test HCAConfig.
        """
        cls.swagger_url = "test_swagger_url"
        cls.open_fn_name = "builtins.open"
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

    def test_swagger_client_refresh(self):
        """Instantiates a modified DSS client that only makes 1 second expiration tokens, forcing it to refresh."""
        dss = TestTokenDSSClient(swagger_url='https://dss.dev.data.humancellatlas.org/v1/swagger.json')
        assert dss._authenticated_session is None

        # we use collections to test because it's an authenticated endpoint
        r = dss.get_collections()
        assert 'collections' in r
        token_one = dss._authenticated_session.token['access_token']
        expires_at = dss._authenticated_session.token['expires_at'] - time.time()
        assert expires_at < 1

        time.sleep(2)  # wait out the 1 second expiration token

        r = dss.get_collections()
        assert 'collections' in r
        token_two = dss._authenticated_session.token['access_token']
        expires_at = dss._authenticated_session.token['expires_at'] - time.time()
        assert expires_at < 1

        assert token_one != token_two  # make sure it requested with two different tokens

    def test_swagger_client_no_refresh(self):
        """
        Instantiates the normal DSSClient with a 3600 second expiration token so that we can check
        that it successfully uses the same token for both requests.
        """
        dss = DSSClient(swagger_url='https://dss.dev.data.humancellatlas.org/v1/swagger.json')
        assert dss._authenticated_session is None

        # we use collections to test because it's an authenticated endpoint
        r = dss.get_collections()
        assert 'collections' in r
        token_one = dss._authenticated_session.token['access_token']
        expires_at = dss._authenticated_session.token['expires_at'] - time.time()
        assert expires_at < 3600
        assert expires_at > 3590

        time.sleep(2)

        r = dss.get_collections()
        assert 'collections' in r
        token_two = dss._authenticated_session.token['access_token']
        expires_at = dss._authenticated_session.token['expires_at'] - time.time()
        assert expires_at < 3600
        assert expires_at > 3590

        assert token_one == token_two  # we used one long-lived token for both requests


if __name__ == "__main__":
    unittest.main()
