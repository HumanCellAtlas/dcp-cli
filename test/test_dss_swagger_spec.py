#!/usr/bin/env python
# coding: utf-8

import unittest
import requests
from hca.util.compat import USING_PYTHON2

import hca.dss

if USING_PYTHON2:
    import mock
    from mock import mock_open
else:
    from unittest import mock
    from unittest.mock import mock_open


class TestDssSwaggerSpec(unittest.TestCase):
    client = hca.dss.DSSClient()
    swagger_url = ""
    dummy_response = None
    open_fn_name = "__builtin__.open" if USING_PYTHON2 else "builtins.open"

    def setUp(self):
        self.client.__class__._swagger_spec = None
        self.client._spec_valid_for_days = 1
        self.swagger_url = "test_swagger_url"
        self.client._session = requests.Session()
        self.client.config.__dict__.update({
            'DSSClient': {
                'swagger_url': self.swagger_url
            },
            'swagger_filename': "test_filename"
        })
        self.dummy_response = requests.models.Response()
        self.dummy_response._content = b'{"swagger": ""}'
        self.dummy_response.status_code = 200

    def tearDown(self):
        self.client.__class__._swagger_spec = None

    def test_get_swagger_spec_new(self):
        with mock.patch('os.path.exists') as mock_exists, \
             mock.patch('hca.dss.SwaggerClient._get_days_since_last_modified') as mock_days_since_last_modified, \
             mock.patch('os.makedirs') as mock_makedirs, \
             mock.patch('requests.Session.get') as mock_get, \
             mock.patch('hca.dss.SwaggerClient.load_swagger_json'), \
             mock.patch(self.open_fn_name, mock_open()) as open_mock:
                mock_exists.return_value = False
                mock_days_since_last_modified.return_value = 0
                mock_get.return_value = self.dummy_response

                test = self.client.swagger_spec
                self.assertTrue(mock_makedirs.called)
                self.assertTrue(mock_get.calledWith(self.swagger_url))
                self.assertTrue(open_mock().write.calledWith(self.dummy_response._content))

    def test_get_swagger_spec_cache_valid(self):
        with mock.patch('os.path.exists') as mock_exists, \
             mock.patch('hca.dss.SwaggerClient._get_days_since_last_modified') as mock_days_since_last_modified, \
             mock.patch('os.makedirs') as mock_makedirs, \
             mock.patch('requests.Session.get') as mock_get, \
             mock.patch('hca.dss.SwaggerClient.load_swagger_json'), \
             mock.patch(self.open_fn_name, mock_open()) as open_mock:
                mock_exists.return_value = True
                mock_days_since_last_modified.return_value = 0
                mock_get.return_value = self.dummy_response

                test = self.client.swagger_spec
                self.assertFalse(mock_makedirs.called)
                self.assertFalse(mock_get.called)
                self.assertFalse(open_mock().write.called)

    def test_get_swagger_spec_cache_expired(self):
        with mock.patch('os.path.exists') as mock_exists, \
             mock.patch('hca.dss.SwaggerClient._get_days_since_last_modified') as mock_days_since_last_modified, \
             mock.patch('os.makedirs') as mock_makedirs, \
             mock.patch('requests.Session.get') as mock_get, \
             mock.patch('hca.dss.SwaggerClient.load_swagger_json'), \
             mock.patch(self.open_fn_name, mock_open()) as open_mock:
                    mock_exists.return_value = True
                    mock_days_since_last_modified.return_value = 2
                    mock_get.return_value = self.dummy_response

                    test = self.client.swagger_spec
                    self.assertTrue(mock_get.calledWith(self.swagger_url))
                    self.assertTrue(open_mock().write.calledWith(self.dummy_response._content))


if __name__ == '__main__':
    unittest.main()
