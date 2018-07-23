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
    dummy_response = None
    swagger_url = "https://dss.data.humancellatlas.org/v1/swagger.json"
    swagger_filename = "test_swagger_filename"
    open_fn_name = "__builtin__.open" if USING_PYTHON2 else "builtins.open"
    saved_swagger_url = client.config['DSSClient'].swagger_url

    def setUp(self):
        self.client.__class__._swagger_spec = None
        self.client._spec_valid_for_days = 1
        self.client._session = requests.Session()
        self.client.config['DSSClient'].swagger_url = self.swagger_url
        self.dummy_response = requests.models.Response()
        self.dummy_response._content = b'{"swagger": ""}'
        self.dummy_response.status_code = 200

    def tearDown(self):
        self.client.config['DSSClient'].swagger_url = self.saved_swagger_url
        if "swagger_filename" in self.client.config:
            self.client.config.pop("swagger_filename")
        self.client.__class__._swagger_spec = None

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
                mock_get.return_value = self.dummy_response

                test = self.client.swagger_spec
                self.assertTrue(mock_makedirs.called)
                mock_get.assert_called_with(self.swagger_url)
                mock_atomic_write.assert_called_with(mock.ANY,
                                                     mock.ANY,
                                                     self.dummy_response._content)

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
                mock_get.return_value = self.dummy_response

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
                mock_get.return_value = self.dummy_response

                test = self.client.swagger_spec
                mock_get.assert_called_with(self.swagger_url)
                mock_atomic_write.assert_called_with(mock.ANY,
                                                     mock.ANY,
                                                     self.dummy_response._content)

    def test_get_swagger_spec_local_config(self):
        with mock.patch('os.makedirs') as mock_makedirs, \
                mock.patch('requests.Session.get') as mock_get, \
                mock.patch('hca.dss.SwaggerClient.load_swagger_json'), \
                mock.patch('hca.util.fs.atomic_write') as mock_atomic_write, \
                mock.patch(self.open_fn_name, mock_open()):
            self.client.config.swagger_filename = self.swagger_filename

            test = self.client.swagger_spec
            self.assertFalse(mock_makedirs.called)
            self.assertFalse(mock_get.called)
            self.assertFalse(mock_atomic_write.called)
